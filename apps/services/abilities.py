import threading
from datetime import datetime, timedelta

from apps.config import settings, logger
from apps.utils.cache import RedisCache
from apps.worker.celery_worker import start_video_task


class VideoTaskServer:
    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.cache = RedisCache(settings.redis_url)
        self.timer = None  # 定时器对象

    def set(self, status, ex=None):
        for info in self.cfg.videoInfo:
            openid = f"analyseId:{info.analyseId}"
            self.cache.set(openid, status, ex=ex)

    def stop(self):
        self.set(0)
        if self.timer:
            self.timer.cancel()  # 取消定时器

    def start(self):
        start_time = datetime.strptime(str(self.cfg.startTime), "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(str(self.cfg.endTime), "%Y-%m-%d %H:%M:%S")
        now_time = datetime.now()
        ex = int((end_time - now_time).total_seconds())

        if end_time < now_time:
            logger.info("任务结束时间小于当前时间，任务忽略")
            return

        if ex <= 0:
            logger.info("任务结束时间大于任务开始时间，任务忽略")
            return

        self.set(1, ex=ex)
        kwargs = self.cfg.dict()
        kwargs['startTime'] = start_time
        kwargs['endTime'] = end_time

        logger.info("算法调用开始--------")
        self.timer = threading.Timer(0, self._start_task)  # 初始延迟设为0
        self.timer.start()

    def _start_task(self):
        start_video_task.apply_async(args=[self.cfg.dict()])
        interval = timedelta(seconds=self.cfg.interval)  # 任务执行间隔
        self.timer = threading.Timer(interval.total_seconds(), self._start_task)
        self.timer.start()

    def delete(self):
        self.set(2)
        if self.timer:
            self.timer.cancel()
