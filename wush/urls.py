from django.conf.urls import url

import wush.views

urlpatterns = [
    url(r'key/$', wush.views.vapid_public_key, name='vapid_public_key'),
    url(r'notify/$', wush.views.send_push_notification, name='send_notification'),
]
