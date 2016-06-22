from django.conf.urls import url, patterns, include

import wush.views

urlpatterns = patterns('',
    url(r'notify/$', wush.views.send_push_notification, name='send_notification'),
)
