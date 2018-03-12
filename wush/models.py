from django.db import models
from django.conf import settings


PLATFORM_CHOICES = (
    ("android", "android"),
    ("ios", "ios"),
    # Web Push
    ("firefox", "firefox"),
    ("chrome", "chrome"),
)

class DeviceToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.TextField()
    platform = models.CharField(choices=PLATFORM_CHOICES, max_length=20)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "token", "platform")

    def __str__(self):
        return "{0}: {1}".format(self.user.username, self.platform)

    def __unicode__(self):
        return self.__str__()
