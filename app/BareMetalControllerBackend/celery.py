# coding:utf8
from __future__ import absolute_import

import os

from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
from BareMetalControllerBackend.conf.env import EnvConfig

env_config = EnvConfig()

# yourprojectname代表你工程的名字，在下面替换掉
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BareMetalControllerBackend.settings')
app = Celery(main=env_config.celery_main, broker=env_config.celery_broker, backend=env_config.celery_backend)
# app = Celery(main="job_executor", broker='pyamqp://admin:admin@10.200.2.187:5672', backend='pyamqp://admin:admin@10.200.2.187:5672')

# Using a string here means the worker will not have to
# pickle the object when using Windows.

class Config:
    CELERY_ENABLE_UTC = True
    CELERY_TASK_PROTOCOL = 1

app.config_from_object(Config)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
# app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
