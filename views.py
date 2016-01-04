import django
django.setup()

import json
import redis
import rq
import requests
import functools
import tornado

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.decorators.http import require_POST

from .models import DeviceToken

from .apns import APNS


REDIS_CLIENT = redis.Redis(settings.REDIS_HOST, settings.REDIS_PORT, db=0)


@csrf_exempt
@require_POST
def send_push_notification(request):
    queue = rq.Queue(connection=REDIS_CLIENT)
    to_username = request.POST.get("to")
    message = request.POST.get("body")
    apids = DeviceToken.objects.filter(user__username=to_username)
    android_apids = apids.filter(platform="android")
    ios_apids = apids.filter(platform="ios")

    if android_apids.count():
        queue.enqueue(queue_push_android, android_apids, message)

    if ios_apids.count():
        queue.enqueue(queue_push_ios, ios_apids, message)

    return JsonResponse({"success": True})


def queue_push_android(apids, message):
    apids_to_clear = []

    username = apids[0].user.username
    push_payload = json.dumps({
        "registration_ids": list(apids.values_list("token", flat=True)),
        "data": {
            "username": username,
            "title": message
        }})
    response = requests.post(settings.GCM_URL, data = push_payload,
                             headers={
                                 "Authorization": "key={0}".format(settings.GCM_KEY),
                                 "Content-Type": "application/json"
                            })
    results = response.json()["results"]
    for idx, result in enumerate(results):
        if result.get("error") and result["error"] == "NotRegistered":
            apids_to_clear.append(apids[idx])

    # Remove unregistered ids
    DeviceToken.objects.filter(token__in=apids_to_clear).delete()


def queue_push_ios(apids, message):
    apns = APNS(debug=settings.DEBUG, certfile=settings.APNS_CERTFILE)
    apns_payload = []

    username = apids[0].user.username
    apns_payload.append(({
        "aps": {
            "alert": message,
            "badge": "auto",
            "sound": "default",
        },
        "username": username
    }, list(apids.values_list('token', flat=True))))
    partial_fn = functools.partial(apns.send_notifications, apns_payload)
    tornado.ioloop.IOLoop.instance().run_sync(partial_fn)
