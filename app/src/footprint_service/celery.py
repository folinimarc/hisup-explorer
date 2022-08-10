# footprint_service/celery.py

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
app = Celery("footprint_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
