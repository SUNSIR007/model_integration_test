import logging

import celery.signals
from celery import Celery
from celery.schedules import crontab
from apps.config import celery_config

celery_app = Celery()

celery_app.config_from_object(celery_config)

celery_app.conf.beat_schedule = {
    'delete_tmp_files': {
        'task': 'apps.worker.celery_worker.delete_tmp_folder',
        'schedule': crontab(hour='0', minute='0'),  # 每天凌晨执行,
    },
}


@celery.signals.setup_logging.connect
def on_celery_setup_logging(**kwargs):
    logger = logging.getLogger('apps.worker.run_tasks_scheduler')
    if not logger.handlers:
        handler = logging.FileHandler('celery_log.log')
        formatter = logging.Formatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
