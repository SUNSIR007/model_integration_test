from datetime import datetime

import pytz
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import Session, relationship
from typing import List

from apps.database import Base

tz = pytz.timezone('Asia/Shanghai')


class Camera(Base):
    __tablename__ = "cameras"

    camera_id = Column(Integer, primary_key=True, autoincrement=True, doc="主键")
    name = Column(String(255), nullable=False, doc="摄像头名称")
    address = Column(String(255), nullable=False, doc="摄像头地址")
    status = Column(String(255), nullable=False, default="在线", doc="摄像头状态")
    channelNum = Column(Integer, nullable=False, doc="通道数量")
    protocol = Column(String(255), nullable=False, doc="协议")
    url = Column(String(255), nullable=False, doc="URL")
    ip = Column(String(255), nullable=False, doc="IP 地址")
    port = Column(String(255), nullable=False, doc="端口")
    username = Column(String(255), doc="用户名")
    password = Column(String(255), doc="密码")
    createTime = Column(DateTime, default=datetime.now(tz), doc="创建时间")
    updateTime = Column(DateTime, default=datetime.now(tz), onupdate=datetime.now(tz), doc="更新时间")
    algorithms = relationship("Algorithm", back_populates="camera")

    @classmethod
    def create(cls, data: dict) -> 'Camera':
        return cls(**data)

    @classmethod
    def query(cls, session: Session, **kwargs) -> List['Camera']:
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

    def get_video_stream_url(self):
        """
        获取监控视频流地址
        """
        protocol = self.protocol.lower()
        username = self.username if self.username else ""
        password = self.password if self.password else ""
        ip = self.ip
        port = self.port
        url = self.url

        video_stream_url = f"{protocol}://{username}:{password}@{ip}:{port}/{url}"

        return video_stream_url
