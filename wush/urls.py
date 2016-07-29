from django.conf.urls import url

import wush.views

urlpatterns = [
    url(r'notify/$', wush.views.send_push_notification, name='send_notification'),
]
