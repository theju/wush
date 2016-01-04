import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import DeviceToken
from core.apns import APNSFeedback


class Command(BaseCommand):
    help = "Remove inactive iOS Device Tokens"
    can_import_settings = True

    def handle(self, *args, **options):
        since_date = datetime.datetime.now() - datetime.timedelta(days=1)
        apns_feedback = APNSFeedback(debug=settings.DEBUG,
                                     certfile=settings.APNS_CERTFILE)
        device_tokens = apns_feedback.fetch(since_date)
        if device_tokens:
            apids = DeviceToken.objects.filter(token__in=device_tokens,
                                               platform='ios')
            apids.delete()
