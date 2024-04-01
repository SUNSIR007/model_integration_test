#!/bin/bash


# 启动FastAPI
uvicorn apps:app --host 172.20.10.3 --port 3000 &

# 启动Celery
celery -A apps.worker.celery_app worker -l INFO -B -s /tmp/celerybeat-schedule -P threads

# 线程池
# celery -A apps.worker.celery_app worker -l INFO -P threads
# 进程池
# celery -A apps.worker.celery_app worker -l INFO -P solo
# 启用监控
# celery -A apps.worker.celery_app flower
