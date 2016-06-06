import django
django.setup()

import json
import redis
import rq
import requests
import time

from pywebpush import WebPusher
from hyper.contrib import HTTP20Adapter

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.decorators.http import require_POST

from .models import DeviceToken


REDIS_CLIENT = redis.Redis(settings.REDIS_HOST, settings.REDIS_PORT, db=0)


@csrf_exempt
@require_POST
def send_push_notification(request):
    queue = rq.Queue(connection=REDIS_CLIENT)
    to_username = request.POST.get("to")
    # Json encoded body
    message = request.POST.get("body")

    apids = DeviceToken.objects.filter(user__username=to_username)
    android_apids = apids.filter(platform="android")
    ios_apids = apids.filter(platform="ios")
    firefox_apids = apids.filter(platform="firefox")
    chrome_apids = apids.filter(platform="chrome")

    if android_apids.count():
        queue.enqueue(queue_push_android, android_apids, message)

    if ios_apids.count():
        queue.enqueue(queue_push_ios, ios_apids, message)

    if firefox_apids.count():
        queue.enqueue(queue_push_firefox, firefox_apids, message)

    if chrome_apids.count():
        queue.enqueue(queue_push_chrome, chrome_apids, message)

    return JsonResponse({"success": True})


def queue_push_android(apids, message):
    apids_to_clear = []

    push_payload = json.dumps({
        "registration_ids": list(apids.values_list("token", flat=True)),
        "data": json.loads(message)
    })
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
    apids_to_clear = []
    if settings.DEBUG == True:
        apns_host = "https://api.development.push.apple.com"
    else:
        apns_host = "https://api.push.apple.com"

    req_session = requests.Session()
    req_session.mount(apns_host, HTTP20Adapter())
    ttl = 7 * 86400
    data = json.loads(message)
    for apid in apids:
        payload = {
            "aps": {
                "alert": data["title"],
                "badge": "auto",
                "sound": "default",
            }
        }
        payload.update(data)
        url = "{0}/3/device/{1}".format(apns_host, apid.token)
        response = req_session.post(
            url,
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "apns-expiration": str(int(time.time()) + ttl),
                "apns-topic": settings.APNS_TOPIC
            },
            cert=settings.APNS_CERTFILE
        )
        if response.status_code == 410:
            apids_to_clear.append(apid)

    # Remove unregistered ids
    for apid in apids_to_clear:
        apid.delete()


def queue_push_chrome(apids, message):
    payload_data = json.loads(message)
    ttl = 7 * 86400
    apids_to_clear = []
    headers = {
        "Authorization": settings.GCM_KEY
    }
    for apid in apids:
        subscription = json.loads(apid.token)
        wp = WebPusher(subscription)
        response = wp.send(json.dumps(payload_data), headers=headers, ttl=ttl)

        if response.status_code == 400:
            content = response.content
            if content.find("UnauthorizedRegistration") >= 0:
                apids_to_clear.append(apid)

    # Remove unregistered ids
    for apid in apids_to_clear:
        apid.delete()


def queue_push_firefox(apids, message):
    payload_data = json.loads(message)
    ttl = 7 * 86400
    apids_to_clear = []
    for apid in apids:
        subscription = json.loads(apid.token)
        wp = WebPusher(subscription)
        response = wp.send(json.dumps(payload_data), ttl=ttl)
        if response.status_code == 410:
            apids_to_clear.append(apid)

    # Remove unregistered ids
    for apid in apids_to_clear:
        apid.delete()
