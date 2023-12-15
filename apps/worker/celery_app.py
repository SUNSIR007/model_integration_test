import os
import sqlite3

from celery import Celery
from celery.schedules import crontab

from apps.config import celery_config
from apps.config import logger

celery_app = Celery()

celery_app.config_from_object(celery_config)

celery_app.conf.beat_schedule = {
    'delete_tmp_files': {
        'task': 'apps.worker.celery_worker.clean_folders_task',
        'schedule': crontab(hour='0', minute='0'),  # 每天凌晨执行,
    },
}


@celery_app.start()
def initialize_database():
    db_path = './model_integration.db'
    sql_file_path = './init.sql'

    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        # 创建数据库文件
        open(db_path, 'w').close()

        # 连接数据库
        conn = sqlite3.connect(db_path)

        # 执行初始化 SQL 文件
        with open(sql_file_path, 'r') as file:
            sql_script = file.read()
            conn.executescript(sql_script)

        # 关闭数据库连接
        conn.close()

        logger.info("Database initialized successfully.")
    else:
        logger.info("Database already exists. Skipping initialization.")
