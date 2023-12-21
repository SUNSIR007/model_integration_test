from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CameraBase(BaseModel):
    name: Optional[str]
    address: Optional[str]
    latitude: Optional[str]
    longitude: Optional[str]
    status: Optional[bool]
    channelNum: Optional[str]
    protocol: Optional[str]
    url: Optional[str]
    ip: Optional[str]
    port: Optional[str]
    username: Optional[str]
    password: Optional[str]
    video_url: Optional[str]

    class Config:
        orm_mode = True


class CameraCreate(CameraBase):
    name: str
    status: bool
    protocol: str
    url: str
    ip: str
    port: str


class CameraInfo(CameraBase):
    camera_id: Optional[int]
    createTime: Optional[datetime]


class AlgorithmConfig(BaseModel):
    algorithmId: int
    status: Optional[bool] = 0
    startHour: Optional[int]
    startMinute: Optional[int]
    endHour: Optional[int]
    endMinute: Optional[int]
    frameFrequency: Optional[int]
    alamInterval: Optional[int]
    conf: Optional[float]
    selected_region: Optional[str]
    intersection_ratio_threshold: Optional[float]
