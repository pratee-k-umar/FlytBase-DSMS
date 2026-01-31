"""
Celery Configuration
"""

import os

from celery import Celery

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dsms.conf.settings.development")

app = Celery("dsms")

# Load config from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all apps
app.autodiscover_tasks(["dsms.tasks"])


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
