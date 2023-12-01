import threading
from datetime import timedelta

from apps.config import logger, settings
from apps.schemas.video_task import VideoTaskConfig
from apps.worker.celery_worker import start_video_task


class VideoTaskServer:
    def __init__(self):
        self.timer = None

    def start(self, config: VideoTaskConfig):
        logger.info("算法异步调用--------")
        self.timer = threading.Timer(0, self._start_task, args=[config])  # 初始延迟设为0
        self.timer.start()

    def _start_task(self, config: VideoTaskConfig):
        start_video_task.apply_async(args=[config.__dict__], queue=settings.celery_quene_name)
        interval = timedelta(seconds=config.interval)  # 任务执行间隔
        self.timer = threading.Timer(interval.total_seconds(), self._start_task, args=[config])
        self.timer.start()
