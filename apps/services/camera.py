from celery.result import AsyncResult

from apps.config import logger, settings
from apps.schemas.video_task import VideoTaskConfig
from apps.worker.celery_worker import start_video_task


class VideoTaskServer:
    def __init__(self):
        self.task_id = None

    def start(self, config: VideoTaskConfig):
        logger.info(f"算法识别任务开始----------------------------")
        task_result = start_video_task.apply_async(args=[config.__dict__], queue=settings.celery_quene_name)
        self.task_id = task_result.id
        return task_result.id

    def stop(self):
        try:
            result = AsyncResult(self.task_id)
            result.revoke(terminate=True)
            logger.info(f"Task with ID {self.task_id} stopped successfully.")
            return True
        except Exception as e:
            logger.error(f"Error stopping task with ID {self.task_id}: {e}")
            return False

    def delete(self):
        try:
            result = AsyncResult(self.task_id)
            result.forget()
            logger.info(f"Task with ID {self.task_id} deleted successfully.")
            return True
        except Exception as e:
            logger.error(f"Error deleting task with ID {self.task_id}: {e}")
            return False
