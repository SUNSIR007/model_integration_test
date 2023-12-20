import base64
import os
import time
import datetime

import cv2
import httpx
import numpy as np
from sqlalchemy.orm import Session

from apps.config import logger, settings
from apps.detection.infer import Detector
from apps.models import Box
from apps.models.camera import CameraAlgorithmAssociation
from apps.utils.box import delete_folders_before_date, get_disk_usage, get_disk_total
from apps.utils.save_alarm import save_alarm
from apps.worker.celery_app import celery_app
from apps.database import get_db_session


def is_within_time_range(start_hour: int, start_minute: int, end_hour: int, end_minute: int):
    """判断当前时间是否在指定范围"""
    current_time = datetime.datetime.now().time()

    start_time = datetime.time(start_hour, start_minute)
    end_time = datetime.time(end_hour, end_minute)

    return start_time <= current_time <= end_time


def get_algo_info(session: Session, algorithm_id: int, camera_id: int):
    algorithm = session.query(CameraAlgorithmAssociation).filter_by(algorithm_id=algorithm_id,
                                                                    camera_id=camera_id).first()

    status = algorithm.status
    frequency = algorithm.frameFrequency
    interval = algorithm.alamInterval
    conf = algorithm.conf
    selected_region = np.array(list(map(int, algorithm.selected_region.split(','))))
    intersection_ratio_threshold = algorithm.intersection_ratio_threshold
    res = is_within_time_range(int(algorithm.startHour),
                               int(algorithm.startMinute),
                               int(algorithm.endHour),
                               int(algorithm.endMinute))
    session.close()
    return status, frequency, interval, conf, selected_region, intersection_ratio_threshold, res


def get_return(session: Session):
    """获取告警结果回传地址,token"""
    box = session.query(Box).first()
    url, token = box.return_url, box.return_token
    session.close()
    return url, token


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


def authentication_required(func):
    def wrapper(*args, **kwargs):
        access_token = kwargs.get('access_token', '')

        # 如果提供了 access_token，则加入参数中
        if access_token:
            # 在头部包含鉴权信息
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            # 将头部添加到 kwargs 中
            kwargs['headers'] = headers

        return func(*args, **kwargs)

    return wrapper


@authentication_required
def upload_analyse_result(**kwargs):
    """上传视频流分析结果"""
    output_file = kwargs.get('output_file', '')
    process_image_data = None

    if output_file:
        with open(output_file, 'rb') as osd_fr:
            process_image_data = str(base64.b64encode(osd_fr.read()), encoding='utf-8')

    _json = {
        "alarmName": kwargs.get('alarmName', ''),
        "analyseTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ImageData": process_image_data
    }

    try:
        logger.info("开始上传分析结果-------------------------")

        httpx.post(
            url=kwargs.get('return_url', ''),
            json=_json,
            timeout=10,
            headers=kwargs.get('headers', {})
        )

        logger.info("分析结果上传完成--------------------------")

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
    logger.info(f"视频流地址：{video_url}")

    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    input_dir = os.path.join(settings.data_dir, "input", current_date)
    output_dir = os.path.join(settings.data_dir, "output", current_date)
    create_directory(input_dir)
    create_directory(output_dir)
    last_upload_time = None
    model_type = kwg['model_type']
    yolo_processor = Detector('apps/detection/weights/' + str(model_name), model_type)

    while True:
        return_url, access_token = get_return(session)
        status, frequency, interval, conf, selected_region, intersection_ratio_threshold, res = get_algo_info(
            session, algorithm_id, camera_id)
        if not status:
            logger.warn("算法未启用-----------------------------------")
            break
        if not res:
            logger.warn("当前时间不在分析时段----------------------------")
        else:
            frame = screenshot(video_url)
            if frame is not None:
                current_time = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))
                filename = f"{algorithm_id}-{current_time}.jpg"
                input_file = os.path.join(input_dir, filename)
                output_file = os.path.join(output_dir, filename)
                cv2.imwrite(input_file, frame)
                try:
                    # 算法调用
                    classnames = yolo_processor.process(input_file, output_file, conf, selected_region,
                                                        intersection_ratio_threshold)
                    if classnames:
                        save_alarm(name, model_name, algorithm_id, camera_id, input_file, output_file)

                        if return_url:
                            if last_upload_time is None or (time.time() - last_upload_time) >= interval:
                                upload_analyse_result(
                                    **{
                                        'alarmName': name,
                                        'output_file': output_file,
                                        'return_url': return_url,
                                        'access_token': access_token
                                    }
                                )
                                last_upload_time = time.time()

                except Exception as e:
                    logger.error(f"Error in model predict: {e}")
            else:
                logger.info("未截取到相关图片----------------------------")

        # 抽帧间隔
        time.sleep(frequency)


@celery_app.task
def clean_folders_task():
    session = next(get_db_session())
    box = session.query(Box).first()
    usage_percentage = get_disk_usage() / get_disk_total() * 100
    if usage_percentage > box.storage_threshold:
        target_date = datetime.datetime.now() - datetime.timedelta(days=box.storagePeriod)
        delete_folders_before_date(base_folder=box.data_folder, target_date=target_date)
