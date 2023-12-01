import logging
import os
from os import environ

from pydantic import RedisDsn, AnyHttpUrl, BaseSettings

logger = logging.getLogger(__name__)
# 日志级别设置为 INFO
logger.setLevel(logging.INFO)
# 添加控制台处理器
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

PROJ_DIR = os.path.dirname(os.path.dirname(__file__))


class ServiceBaseSettings(BaseSettings):
    password: str
    # redis config
    redis_url: RedisDsn
    # mysql config
    db_url: str

    # celery config
    celery_broker_url: str
    celery_quene_name: str
    celery_worker_concurrency: int
    celery_worker_max_tasks_per_child: int

    # 回传结果地址
    return_result_url: AnyHttpUrl

    # 项目路径
    proj_dir: str
    # 文件路径
    data_dir: str


class ProdSettings(ServiceBaseSettings):
    password: str = "1234"
    # redis config
    redis_url: RedisDsn = "redis://127.0.0.1/0"
    # database config
    db_url: str = "mysql://root:aiyouyou.@127.0.0.1:3306:model_integration"

    # celery config
    celery_broker_url: str = "redis://127.0.0.1/1"
    celery_quene_name: str = "model-integration-tasks-prod"
    celery_worker_max_tasks_per_child: int = 2
    celery_worker_concurrency: int = 3

    # 项目路径
    proj_dir: str = PROJ_DIR
    # 文件路径
    data_dir: str = os.path.join(PROJ_DIR, 'data')

    # 回传结果地址
    return_result_url: AnyHttpUrl = 'http://192.168.3.114:8000'

    # jwt config
    # jwt_secret_key default from `openssl rand -hex 32`
    jwt_secret_key: str = "e9fccd82cb91f2dc87097ddf78cf6a50"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_seconds: int = 30
    jwt_refresh_token_expire_days: int = 30

    class Config:
        env_file = ".env.prod"


class LocalSettings(ServiceBaseSettings):
    password: str = "1234"
    # redis config
    redis_url: RedisDsn = "redis://127.0.0.1/0"
    # database config
    db_url: str = "sqlite:///model_integration.db"

    # celery config
    celery_broker_url: str = "redis://127.0.0.1/1"
    celery_quene_name: str = "model-integration-tasks-local"
    celery_worker_max_tasks_per_child: int = 2
    celery_worker_concurrency: int = 3

    # 项目路径
    proj_dir: str = PROJ_DIR
    # 文件路径
    data_dir: str = os.path.join(PROJ_DIR, 'data')

    # 回传结果地址
    return_result_url: AnyHttpUrl = 'http://192.168.3.114:8000'

    # jwt config
    # jwt_secret_key default from `openssl rand -hex 32`
    jwt_secret_key: str = "e9fccd82cb91f2dc87097ddf78cf6a50"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_seconds: int = 30
    jwt_refresh_token_expire_days: int = 30

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
    'include': ['apps.worker.celery_worker'],
    'task_default_queue': settings.celery_quene_name,
    # 消息代理的登录认证方法
    'broker_login_method': 'PLAIN',
    # celery worker并发数
    'worker_concurrency': settings.celery_worker_concurrency,
    # 每个工作进程执行的最大任务数，用于解决内存泄漏问题
    'worker_max_tasks_per_child': settings.celery_worker_max_tasks_per_child,
    # 连接丢失时取消长时间运行的任务
    "worker_cancel_long_running_tasks_on_connection_loss": True,
}
