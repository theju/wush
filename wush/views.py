import json
import requests
import time

import django_rq

from pywebpush import webpush
from hyper.contrib import HTTP20Adapter

from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.decorators.http import require_POST

from .models import DeviceToken

DEFAULT_TTL = getattr(settings, 'DEFAULT_TTL', 7 * 86400)


@csrf_exempt
@require_POST
def send_push_notification(request):
    queue = django_rq.get_queue('default')
    to_username = request.POST.get("to")
    # Json encoded body
    message = request.POST.get("body")

    apids = DeviceToken.objects.filter(user__username=to_username)
    android_apids = apids.filter(platform="android")
    ios_apids = apids.filter(platform="ios")
    firefox_apids = apids.filter(platform="firefox")
    chrome_apids = apids.filter(platform="chrome")

    if android_apids.count():
        queue.enqueue(push_android, android_apids, message)

    if ios_apids.count():
        queue.enqueue(push_ios, ios_apids, message)

    if firefox_apids.count():
        queue.enqueue(push_firefox, firefox_apids, message)

    if chrome_apids.count():
        queue.enqueue(push_chrome, chrome_apids, message)

    return JsonResponse({"success": True})


def push_android(apids, message, ttl=DEFAULT_TTL):
    # TODO: Migrate to FCM
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


def push_ios(apids, message, ttl=DEFAULT_TTL):
    apids_to_clear = []
    if settings.DEBUG == True:
        apns_host = "https://api.development.push.apple.com"
    else:
        apns_host = "https://api.push.apple.com"

    req_session = requests.Session()
    req_session.mount(apns_host, HTTP20Adapter())
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


def push_chrome(apids, message, ttl=DEFAULT_TTL):
    payload_data = json.loads(message)
    apids_to_clear = []
    for apid in apids:
        subscription = json.loads(apid.token)
        vapid_claims = {
            'exp': int(timezone.now().timestamp()) + ttl,
            'sub': ','.join(['{0}:{1}'.format('mailto', ii[1]) for ii in settings.ADMINS])
        }
        response = webpush(
            subscription,
            json.dumps(payload_data),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims=vapid_claims)

        if response.status_code == 400:
            content = response.content
            if content.find("UnauthorizedRegistration") >= 0:
                apids_to_clear.append(apid)

    # Remove unregistered ids
    for apid in apids_to_clear:
        apid.delete()


def push_firefox(apids, message, ttl=DEFAULT_TTL):
    payload_data = json.loads(message)
    apids_to_clear = []
    for apid in apids:
        subscription = json.loads(apid.token)
        vapid_claims = {
            'exp': int(timezone.now().timestamp()) + ttl,
            'sub': ','.join(['{0}:{1}'.format('mailto', ii[1]) for ii in settings.ADMINS])
        }
        response = webpush(
            subscription,
            json.dumps(payload_data),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims=vapid_claims
        )
        if response.status_code == 410:
            apids_to_clear.append(apid)

    # Remove unregistered ids
    for apid in apids_to_clear:
        apid.delete()


def vapid_public_key(request):
    ff = open(settings.VAPID_PUBLIC_KEY).read()
    return HttpResponse(ff, content_type='text/plain')
