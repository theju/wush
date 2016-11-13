import rq
import redis
import django

from django.conf import settings


REDIS_CLIENT = redis.Redis(settings.REDIS_HOST, settings.REDIS_PORT, db=0)


class CustomJob(rq.job.Job):
    def _unpickle_data(self):
        django.setup()
        super(CustomJob, self)._unpickle_data()


class CustomQueue(rq.Queue):
    def __init__(self, *args, **kwargs):
        kwargs["connection"] = REDIS_CLIENT
        kwargs["job_class"] = CustomJob
        super(CustomQueue, self).__init__(*args, **kwargs)
