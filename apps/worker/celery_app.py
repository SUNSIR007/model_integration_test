from celery import Celery
from apps.config import celery_config

celery_app = Celery()

celery_app.config_from_object(celery_config)
