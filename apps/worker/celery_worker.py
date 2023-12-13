import base64
import os
import time
import datetime

import cv2
import httpx
from sqlalchemy.orm import Session

from apps.config import logger
from apps.config import settings
from apps.database import get_db_session
from apps.detection.infer import Detector
from apps.models import Box
from apps.models.camera import CameraAlgorithmAssociation
from apps.utils.save_alarm import save_alarm
from apps.worker.celery_app import celery_app


def is_within_time_range(start_hour: int, start_minute: int, end_hour: int, end_minute: int):
    """判断当前时间是否在指定范围"""
    current_time = datetime.datetime.now().time()

    start_time = datetime.time(start_hour, start_minute)
    end_time = datetime.time(end_hour, end_minute)

    return start_time <= current_time <= end_time


def get_algo_info(session: Session, algorithm_id: int, camera_id: int):
    """判断算法是否可以执行"""
    algorithm = session.query(CameraAlgorithmAssociation).filter_by(algorithm_id=algorithm_id,
                                                                    camera_id=camera_id).first()

    status, frequency, interval = algorithm.status, algorithm.frameFrequency, algorithm.alamInterval
    if not algorithm.status:
        logger.info("算法未启用----------------------------")
        return False
    res = is_within_time_range(int(algorithm.startHour),
                               int(algorithm.startMinute),
                               int(algorithm.endHour),
                               int(algorithm.endMinute))
    if not res:
        logger.info("当前时间不在分析时段----------------------------")
        return False
    session.close()
    return status, frequency, interval


def get_return_url(session: Session):
    """获取告警结果回传地址"""
    box = session.query(Box).first()
    url = box.return_url
    session.close()
    return url


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
    url = kwargs['return_url']
    output_file = kwargs['output_file']
    process_image_data = None
    if output_file:
        with open(kwargs['output_file'], 'rb') as osd_fr:
            process_image_data = str(base64.b64encode(osd_fr.read()), encoding='utf-8')

    _json = {
        "alarmName": kwargs['name'],
        "analyseTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "filename": kwargs['filename'],
        "ImageData": process_image_data,
    }
    try:
        logger.info("开始上传分析结果！")
        httpx.post(
            url=url,
            json=_json,
            timeout=10
        )
        logger.info("分析结果上传完成！")
    except httpx.HTTPError as exc:
        logger.error(exc)


@celery_app.task
def start_video_task(kwg):
    """视频分析任务开始"""
    algorithm_id = kwg["algorithm_id"]
    video_url = kwg["video_stream_url"]
    camera_id = kwg["camera_id"]
    name = kwg["alarm_name"]
    model_name = kwg["model_name"]
    session = next(get_db_session())
    logger.info(f"当前处理视频流地址：{video_url}")

    # 获取当前日期，并创建文件夹路径
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    input_dir = os.path.join(settings.data_dir, "input", current_date)
    output_dir = os.path.join(settings.data_dir, "output", current_date)
    create_directory(input_dir)
    create_directory(output_dir)
    last_upload_time = None

    while True:
        return_url = get_return_url(session)
        status, frequency, interval = get_algo_info(session, algorithm_id, camera_id)
        if status:
            frame = screenshot(video_url)
            if frame is not None:
                current_time = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))
                filename = f"{algorithm_id}-{current_time}.jpg"
                input_file = os.path.join(input_dir, filename)
                output_file = os.path.join(output_dir, filename)
                cv2.imwrite(input_file, frame)
                try:
                    # 算法调用
                    model_type = kwg['model_type']
                    yolo_processor = Detector('apps/detection/weights/' + str(model_name), model_type)
                    classnames = yolo_processor.process(input_file, output_file)
                    if classnames:
                        save_alarm(name, model_name, algorithm_id, camera_id, input_file, output_file)

                        if return_url:
                            if last_upload_time is None or (time.time() - last_upload_time) >= interval:
                                upload_analyse_result(
                                    **{
                                        'alarmName': name,
                                        'modelName': model_name,
                                        'output_file': output_file,
                                        'return_url': return_url
                                    }
                                )
                                logger.info("分析结果回传成功-------------------")
                                last_upload_time = time.time()

                except Exception as e:
                    logger.error(f"Error in model predict: {e}")
            else:
                logger.info("未截取到相关图片----------------------")

        # 抽帧间隔
        time.sleep(frequency)


# @celery_app.task
# def delete_tmp_folder():
#     base_path = "static/data/"
#
#     previous_day = datetime.now() - timedelta(days=7)
#     previous_day_str = previous_day.strftime("%Y-%m-%d")
#
#     input_folder_to_delete = os.path.join(base_path, "input", previous_day_str)
#     output_folder_to_delete = os.path.join(base_path, "output", previous_day_str)
#
#     delete_folder(input_folder_to_delete, "输入")
#     delete_folder(output_folder_to_delete, "输出")
