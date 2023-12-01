from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AlarmRecordCreateReq(BaseModel):
    algorithmId: int
    cameraId: int
    cameraChannelNum: int
    cameraName: str
    address: str
    imageIn: str
    imageOut: str
    algorithmName: str
    alarmTime: Optional[datetime] = None

    class Config:
        orm_mode = True


class UpdateAlarmRecordRequest(BaseModel):
    id: int
    algorithmId: int = None
    cameraId: int = None
    cameraChannelNum: int = None
    cameraName: str = None
    address: str = None
    imageIn: str = None
    imageOut: str = None
    algorithmName: str = None
    alarmTime: datetime = None

    class Config:
        orm_mode = True


class AlarmFilterParams(BaseModel):
    algorithmId: int = None
    cameraId: int = None
    cameraChannelNum: int = None
    cameraName: str = None
    address: str = None
    imageIn: str = None
    imageOut: str = None
    algorithmName: str = None
    alarmTime: str = None
    id: int = None
    createTime: str = None


def get_alarm_records(filter_params: AlarmFilterParams):
    query_params = filter_params.dict(exclude_unset=True)