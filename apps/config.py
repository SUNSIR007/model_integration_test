import logging
import os
from os import environ

from pydantic import BaseSettings

logger = logging.getLogger(__name__)
# 日志级别设置为 INFO
logger.setLevel(logging.INFO)
# 添加控制台处理器
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

PROJ_DIR = os.path.dirname(os.path.dirname(__file__))


class ServiceBaseSettings(BaseSettings):
    # user initial password
    password: str

    # database config
    db_url: str

    # celery config
    celery_broker_url: str
    celery_quene_name: str
    celery_worker_concurrency: int
    celery_worker_max_tasks_per_child: int

    # project path
    proj_dir: str
    # static file path
    data_dir: str

    # GPU device config
    device: str

    # jwt config
    # jwt_secret_key default from `openssl rand -hex 32`
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_seconds: int
    jwt_refresh_token_expire_days: int

    # EasyCVR config
    easycvr_url: str
    easycvr_username: str
    easycvr_password: str


class ProdSettings(ServiceBaseSettings):
    password: str = "1234"

    db_url: str = "sqlite:///model_integration.db"

    # celery config
    celery_broker_url: str = "redis://:byjs666@127.0.0.1/1"
    celery_quene_name: str = "model-integration-tasks-prod"
    celery_worker_max_tasks_per_child: int = 32
    celery_worker_concurrency: int = 16

    proj_dir: str = PROJ_DIR
    data_dir: str = os.path.join('static/data')

    device: str = '0'

    # jwt config
    jwt_secret_key: str = "e9fccd82cb91f2dc87097ddf78cf6a50"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_seconds: int = 300
    jwt_refresh_token_expire_days: int = 30

    # EasyCVR config
    easycvr_url: str = "http://222.88.186.81:23843"
    easycvr_username: str = "easycvr"
    easycvr_password: str = "byjs@2023"

    # 交通拥堵算法参数配置
    base_ppm: float = 0.5  # 像素比
    alpha: float = 0.6  # ppm随像素位置的增长率
    video_fps: int = 30  # 视频帧率
    congestion_threshold: int = 20  # 车流量阈值
    time_window: int = 30  # 交通拥堵车流统计周期（秒）
    average_speed: int = 15  # 车速阈值

    class Config:
        env_file = ".env.prod"


class LocalSettings(ServiceBaseSettings):
    password: str = "1234"

    db_url: str = "sqlite:///model_integration.db"

    celery_broker_url: str = "redis://127.0.0.1/1"
    celery_quene_name: str = "model-integration-tasks-local"
    celery_worker_max_tasks_per_child: int = 32
    celery_worker_concurrency: int = 2

    proj_dir: str = PROJ_DIR
    data_dir: str = os.path.join('static/data')

    device: str = 'cpu'

    jwt_secret_key: str = "e9fccd82cb91f2dc87097ddf78cf6a50"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_seconds: int = 300
    jwt_refresh_token_expire_days: int = 30

    easycvr_url: str = "http://222.88.186.81:23843"
    easycvr_username: str = "easycvr"
    easycvr_password: str = "byjs@2023"

    base_ppm: float = 0.1
    alpha: float = 0.5
    video_fps: int = 30
    congestion_threshold: int = 10
    time_window: int = 20
    average_speed: int = 50

    class Config:
        env_file = ".env.local"


def get_settings() -> ServiceBaseSettings:
    env_name = environ.get("ENV_NAME", "local")
    settings = {
        "prod": ProdSettings(),
        "local": LocalSettings()
    }.get(env_name)

    return settings


# Cache settings
settings = get_settings()

# * celery
celery_config = {
    'broker_url': settings.celery_broker_url,
    'task_serializer': 'json',
    'accept_content': ['json', 'pickle'],
    'result_serializer': 'json',
    'timezone': 'Asia/Shanghai',
    # 在分布式系统中启用协调UTC
    'enable_utc': 'True',
    'broker_connection_retry_on_startup': True,
    'include': ['apps.worker.celery_worker'],
    'task_default_queue': settings.celery_quene_name,
    # 消息代理的登录认证方法
    'broker_login_method': 'PLAIN',
    # 单个 worker 进程的负载，减少系统资源的使用
    'worker_concurrency': settings.celery_worker_concurrency,
    # 每个工作进程最多执行多少个任务后会被重启，用于解决内存泄漏问题
    'worker_max_tasks_per_child': settings.celery_worker_max_tasks_per_child,
    # 连接丢失时取消长时间运行的任务
    "worker_cancel_long_running_tasks_on_connection_loss": True,
}
