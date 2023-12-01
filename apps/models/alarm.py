from datetime import datetime

import pytz
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Session
from typing_extensions import List

from apps.database import Base

tz = pytz.timezone('Asia/Shanghai')


class Alarm(Base):
    __tablename__ = "alarm"

    id = Column(Integer, primary_key=True, autoincrement=True, doc="主键")
    algorithmId = Column(Integer, index=True, nullable=False, doc="算法id")
    cameraId = Column(Integer, nullable=False, doc="摄像头id")
    cameraChannelNum = Column(Integer, doc="摄像头通道")
    cameraName = Column(String(255), doc="摄像头名称")
    address = Column(String(255), doc="地址")
    imageIn = Column(String(255), nullable=False, doc="原始图片")
    imageOut = Column(String(255), nullable=False, doc="报警图片")
    algorithmName = Column(String(255), doc="算法名称")
    alarmTime = Column(DateTime, default=datetime.now(tz), doc="告警时间")
    createTime = Column(DateTime, default=datetime.now(tz), doc="创建时间")

    @classmethod
    def query(cls, session: Session, **kwargs) -> List['Alarm']:
        query = session.query(cls)

        for attr, value in kwargs.items():
            if hasattr(cls, attr):
                query = query.filter(getattr(cls, attr) == value)

        return query.all()

    def update(self, session: Session, data: dict) -> None:
        for key, value in data.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)

        session.commit()

    def delete(self, session: Session) -> None:
        session.delete(self)
        session.commit()
