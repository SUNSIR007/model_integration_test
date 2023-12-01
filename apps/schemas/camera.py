from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class AlgorithmInstance(BaseModel):
    algorithmId: int
    algorithmName: str
    algorithmVersion: str
    algorithmIntro: str
    sdkConfig: str = None


class CameraCreate(BaseModel):
    name: str
    address: str = None
    status: str
    channelNum: int
    protocol: str = None
    url: str = None
    ip: str = None
    port: str = None
    username: str = None
    password: str = None

    class Config:
        orm_mode = True


class CameraInfo(CameraCreate):
    camera_id: int
    createTime: datetime
    relatedAlgorithmInstances: Optional[List[AlgorithmInstance]] = []

    class Config:
        orm_mode = True


class CameraUpdateReq(CameraCreate):
    camera_id: int

    class Config:
        orm_mode = True


class AlgorithmConfig(BaseModel):
    algorithmId: int
    frameFrequency: int = None
    alamInterval: int = None
