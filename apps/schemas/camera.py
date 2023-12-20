from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class AlgorithmInstance(BaseModel):
    algorithmId: int
    algorithmName: str
    algorithmStatus: int
    algorithmInterval: int
    algorithmIntro: str


class CameraCreate(BaseModel):
    name: str
    address: Optional[str]
    status: bool
    channelNum: Optional[str]
    protocol: str
    url: str
    ip: str
    port: str
    username: Optional[str]
    password: Optional[str]
    video_url: Optional[str]

    class Config:
        orm_mode = True


class CameraInfo(CameraCreate):
    camera_id: int
    createTime: datetime
    relatedAlgorithmInstances: Optional[List[AlgorithmInstance]] = []

    class Config:
        orm_mode = True


class CameraUpdateReq(BaseModel):
    name: Optional[str]
    address: Optional[str]
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
