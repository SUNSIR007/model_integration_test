

from celery import Celery
from celery.schedules import crontab

from apps.config import celery_config


celery_app = Celery()

celery_app.config_from_object(celery_config)

celery_app.conf.beat_schedule = {
    'clean_folders_task': {
        'task': 'apps.worker.celery_worker.clean_folders_task',
        'schedule': crontab(hour='0', minute='0'),  # 每天凌晨执行,
    },
}
