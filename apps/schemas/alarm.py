from datetime import datetime
from typing import Optional
from enum import Enum

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


class FilterTime(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class StatisticsType(str, Enum):
    ALARMTYPE = "alarmType"
    TIME = "time"
    PLACE = "place"


class StatisticsInfo(BaseModel):
    filterTime: FilterTime
    statisticTypes: list[StatisticsType]
    startTime: Optional[datetime] = None
    endTime: Optional[datetime] = None
