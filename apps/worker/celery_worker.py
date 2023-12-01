import os
import time
from datetime import datetime

import cv2
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

from apps.config import settings
from apps.database import get_db_session
from apps.detection.infer import Detector
from apps.models import Algorithm
from apps.worker.celery_app import celery_app
from apps.utils.save_alarm import save_alarm

logger = get_task_logger(__name__)


def should_abort_task(session: Session, algorithm_id: int) -> bool:
    """检查算法是否启用，返回 True 表示需要中止任务."""
    algorithm = session.query(Algorithm).filter_by(id=algorithm_id).first()
    logger.info(algorithm.status)

    if algorithm is None:
        logger.warning(f"Algorithm with id {algorithm_id} not found.")
        return True

    if not algorithm.status:
        logger.warning(f"Algorithm with id {algorithm_id} is not enabled.")
        return True
    session.close()
    return False


def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def screenshot(url):
    """视频流抽帧"""
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    if not cap.isOpened():
        cap.release()

    flag, frame = cap.read()
    cap.release()

    return frame


@celery_app.task
def start_video_task(video_task_config):
    """视频分析任务开始"""
    algorithm_id = video_task_config["algorithm_id"]
    camera_id = video_task_config["camera_id"]
    session = next(get_db_session())
    task_id = start_video_task.request.id
    if should_abort_task(session, algorithm_id):
        logger.warning(f"Aborting start_video_task for algorithm_id {algorithm_id}.")
        AsyncResult(task_id).revoke(terminate=True)

    model_name = video_task_config["model_name"]
    # 获取当前日期，并创建文件夹路径
    current_date = datetime.now().strftime('%Y-%m-%d')
    input_dir = os.path.join(settings.data_dir, "input", current_date)
    output_dir = os.path.join(settings.data_dir, "output", current_date)

    create_directory(input_dir)
    create_directory(output_dir)

    try:
        frame = screenshot(video_task_config["video_stream_url"])
        filename = f"{algorithm_id}-{time.time()}.jpg"
        input_file = os.path.join(input_dir, filename)
        output_file = os.path.join(output_dir, filename)

        if frame is None:
            logger.info("未截取到图片")

        cv2.imwrite(input_file, frame)

        # 算法调用
        model_type = video_task_config['model_type']
        yolo_processor = Detector('apps/detection/weights/' + str(model_name), model_type)
        classnames = yolo_processor.process(input_file, output_file)
        if classnames:
            save_alarm(model_name, algorithm_id, camera_id, input_file, output_file)

    except Exception as e:
        logger.error(f"Error in start_video_task: {e}")


# def upload_analyse_result(**kwargs):
#     """上传视频流分析结果"""
#
#     analyse_result_url = 'analysis/api/analyseResult'
#     base_url = settings.return_result_url
#
#     analyse_results = kwargs['analyse_results']
#     process_image_data = None
#     logger.info(analyse_results)
#     if analyse_results:
#         with open(kwargs['output_file'], 'rb') as osd_fr:
#             process_image_data = str(base64.b64encode(osd_fr.read()), encoding='utf-8')
#
#     _json = {
#         "modelName": kwargs['modelName'],
#         "analyseId": kwargs['analyseId'],
#         "analyseTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "analyseResults": analyse_results,
#         "filename": kwargs['filename'],
#         "ImageData": process_image_data,
#     }
#     try:
#         logger.info("开始上传分析结果！")
#         httpx.post(
#             os.path.join(base_url, analyse_result_url.strip('/')),
#             json=_json,
#             timeout=10
#         )
#         logger.info("分析结果上传完成！")
#     except httpx.HTTPError as exc:
#         logger.error(exc)


# @celery_app.task
# def start_video_task(kwg):
#     """视频分析任务开始"""
#     start_time = int(kwg.get('startTime').timestamp())
#     end_time = int(kwg.get('endTime').timestamp())
#
#     video_info = kwg.get('videoInfo')
#     cache = RedisCache(settings.redis_url)
#     model_name = model_config.get(kwg.get('modelName'))
#
#     input_dir = os.path.join(settings.data_dir, "input")
#     output_dir = os.path.join(settings.data_dir, "output")
#     create_directory(output_dir)
#
#     logger.info("current %s" % (time.time()))
#     now_local = datetime.fromtimestamp(int(time.time()))
#     start_datetime = datetime.fromtimestamp(start_time)
#     end_datetime = datetime.fromtimestamp(end_time)
#     # 小于开始时间
#     if now_local < start_datetime:
#         time.sleep(int((start_datetime - now_local).total_seconds()))
#         return
#
#     # 大于结束时间
#     if now_local > end_datetime:
#         return
#
#     if len(video_info) == 0:
#         return
#     try:
#         for info in video_info:
#             # 任务删除或停止
#             analyse_id = info.get('analyseId')
#             logger.info("analyseId is %s" % analyse_id)
#             openid = f"analyseId:{analyse_id}"
#             # 任务停止
#             if cache.get(openid) == 0:
#                 continue
#             elif cache.get(openid) == 2 or cache.get(openid) is None:
#                 video_info.remove(info)
#
#             frame = screenshot(info.get('videoUrl'))
#             filename = f"{analyse_id}-{time.time()}.jpg"
#             input_file = os.path.join(input_dir, filename)
#             output_file = os.path.join(output_dir, filename)
#
#             if frame is None:
#                 logger.info("未截取到图片")
#                 continue
#
#             cv2.imwrite(input_file, frame)
#
#             # 算法调用
#             yolo_processor = YOLOProcessor('apps/detection/weights/' + str(model_name))
#             json_result, _ = yolo_processor.process(input_file, output_file)
#
#             # 上传分析结果
#             upload_analyse_result(
#                 **{
#                     'modelName': model_name,
#                     'analyseId': analyse_id,
#                     'filename': filename,
#                     'output_file': output_file,
#                     'analyse_results': json_result,
#                 }
#             )
#
#             # delete local image data
#             delete_file(input_file)
#             delete_file(output_file)
#
#     except Exception as e:
#         logger.info(e)
