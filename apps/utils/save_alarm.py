from datetime import datetime

import pytz

from apps.database import get_db_session
from apps.models import Alarm, Camera

tz = pytz.timezone('Asia/Shanghai')


def save_alarm(model_name, algorithm_id, camera_id, image_input, image_output):
    session = next(get_db_session())
    camera = session.query(Camera).filter_by(camera_id=camera_id).first()
    alarm_info = {
        "algorithmId": algorithm_id,
        "cameraId": camera_id,
        "cameraChannelNum": camera.channelNum,
        "cameraName": camera.name,
        "address": camera.address,
        "imageIn": image_input,
        "imageOut": image_output,
        "algorithmName": model_name,
        "alarmTime": datetime.now(tz),
        "createTime": datetime.now(tz)
    }
    # 创建新的告警记录对象
    new_alarm = Alarm(**alarm_info)

    # 插入记录到数据库
    session.add(new_alarm)
    session.commit()
