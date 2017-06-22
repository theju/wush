from django.contrib import admin

from .models import DeviceToken

class DeviceTokenAdmin(admin.ModelAdmin):
    list_filter = ["platform"]

admin.site.register(DeviceToken, DeviceTokenAdmin)
