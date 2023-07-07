from __future__ import absolute_import, unicode_literals
import os

from celery import Celery
from django.conf import settings
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')
app.conf.enable_utc = True #False

# app.conf.update(timezone = 'Asia/Kolkata')


app.config_from_object(settings, namespace='CELERY')

# Celery Beat Settings
app.conf.beat_schedule = {
    # 'do-something': {
    #     'task': 'operations.tasks.test_foo',
    #     'schedule': crontab(hour=7, minute=38),
    #     'args': ("hello herrerere",)
    # }
}

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


'''    
    following this tutorial:https://www.youtube.com/watch?v=IcuteHZJlHE
    https://www.youtube.com/watch?v=JYQG7zlLJrE
'''

