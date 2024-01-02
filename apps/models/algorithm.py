from datetime import datetime
from typing import Optional

import pytz
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import Session, relationship

from apps.database import Base

tz = pytz.timezone('Asia/Shanghai')


class Algorithm(Base):
    __tablename__ = "algorithms"

    id = Column(Integer, primary_key=True, autoincrement=True, doc="主键")
    name = Column(String(64), nullable=False, doc="算法名称")
    modelName = Column(String(64), nullable=False, doc="模型名称")
    repoSource = Column(String(255), nullable=False, doc="模型文件路径")
    coverPath = Column(String(255), nullable=False, doc="封面图片路径")
    algorithmIntro = Column(String(255), doc="算法描述")
    modelType = Column(String(255), nullable=False, default="yolov8", doc="算法类型")
    createTime = Column(DateTime, nullable=False, default=datetime.now(tz), doc="创建时间")
    cameras = relationship("Camera", secondary="camera_algorithm_association", back_populates="algorithms")

    @classmethod
    def get_algorithm(cls, session: Session, algorithm_id: int) -> Optional["Algorithm"]:
        return session.query(Algorithm).filter_by(id=algorithm_id).first()

    def update(self, session: Session, data: dict) -> None:
        for key, value in data.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)

        session.commit()
