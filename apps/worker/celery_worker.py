import base64
import os
import time
from datetime import datetime, timedelta

import cv2
import httpx
from sqlalchemy.orm import Session

from apps.config import logger
from apps.config import settings
from apps.database import get_db_session
from apps.detection.infer import Detector
from apps.models.camera import CameraAlgorithmAssociation
from apps.utils.save_alarm import save_alarm
from apps.worker.celery_app import celery_app


def get_algo_status(session: Session, algorithm_id: int, camera_id: int) -> bool:
    algorithm = session.query(CameraAlgorithmAssociation).filter_by(algorithm_id=algorithm_id,
                                                                    camera_id=camera_id).first()
    logger.info(algorithm.status)
    status = 0
    if algorithm and algorithm.status:
        status = algorithm.status
    session.close()
    return status


def screenshot(url):
    """视频流抽帧"""
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    if not cap.isOpened():
        cap.release()

    flag, frame = cap.read()
    cap.release()

    return frame


def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def delete_folder(folder_path, folder_type):
    """
    删除指定类型的文件夹
    :param folder_path: 文件夹路径
    :param folder_type: 文件夹类型，用于日志输出
    """
    if os.path.exists(folder_path):
        try:
            os.rmdir(folder_path)
            logger.info(f"已删除{folder_type}文件夹: {folder_path}")
        except Exception as e:
            logger.error(f"删除{folder_type}文件夹时发生错误: {e}")
    else:
        logger.info(f"{folder_type}文件夹不存在: {folder_path}")


def upload_analyse_result(**kwargs):
    """上传视频流分析结果"""

    analyse_result_url = 'analysis/api/analyseResult'
    base_url = settings.return_result_url

    analyse_results = kwargs['analyse_results']
    process_image_data = None
    logger.info(analyse_results)
    if analyse_results:
        with open(kwargs['output_file'], 'rb') as osd_fr:
            process_image_data = str(base64.b64encode(osd_fr.read()), encoding='utf-8')

    _json = {
        "modelName": kwargs['modelName'],
        "analyseId": kwargs['analyseId'],
        "analyseTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "analyseResults": analyse_results,
        "filename": kwargs['filename'],
        "ImageData": process_image_data,
    }
    try:
        logger.info("开始上传分析结果！")
        httpx.post(
            os.path.join(base_url, analyse_result_url.strip('/')),
            json=_json,
            timeout=10
        )
        logger.info("分析结果上传完成！")
    except httpx.HTTPError as exc:
        logger.error(exc)


@celery_app.task
def start_video_task(video_task_config):
    """视频分析任务开始"""
    algorithm_id = video_task_config["algorithm_id"]
    video_url = video_task_config["video_stream_url"]
    camera_id = video_task_config["camera_id"]
    name = video_task_config["alarm_name"]
    model_name = video_task_config["model_name"]
    frame_frequency = video_task_config["interval"]
    session = next(get_db_session())
    logger.info(f"当前处理视频流地址：{video_url}")

    # 获取当前日期，并创建文件夹路径
    current_date = datetime.now().strftime('%Y-%m-%d')
    input_dir = os.path.join(settings.data_dir, "input", current_date)
    output_dir = os.path.join(settings.data_dir, "output", current_date)
    create_directory(input_dir)
    create_directory(output_dir)

    while True:
        # 判断算法开启状态
        status = get_algo_status(session, algorithm_id, camera_id)
        if not status:
            logger.info(f"算法{video_task_config['model_name']}预测任务结束----------------------------")
            break

        frame = screenshot(video_url)
        if frame is not None:
            current_time = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))
            filename = f"{algorithm_id}-{current_time}.jpg"
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)
            cv2.imwrite(input_file, frame)
            try:
                # 算法调用
                model_type = video_task_config['model_type']
                yolo_processor = Detector('apps/detection/weights/' + str(model_name), model_type)
                classnames = yolo_processor.process(input_file, output_file)
                if classnames:
                    save_alarm(name, model_name, algorithm_id, camera_id, input_file, output_file)

            except Exception as e:
                logger.error(f"Error in model predict: {e}")
        else:
            logger.info("未截取到相关图片----------------------")

        time.sleep(frame_frequency)


@celery_app.task
def delete_tmp_folder():
    base_path = "static/data/"

    previous_day = datetime.now() - timedelta(days=1)
    previous_day_str = previous_day.strftime("%Y-%m-%d")

    input_folder_to_delete = os.path.join(base_path, "input", previous_day_str)
    output_folder_to_delete = os.path.join(base_path, "output", previous_day_str)

    delete_folder(input_folder_to_delete, "输入")
    delete_folder(output_folder_to_delete, "输出")


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
