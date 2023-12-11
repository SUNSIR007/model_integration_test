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
    version = Column(String(32), doc="算法版本")
    repoSource = Column(String(255), nullable=False, doc="算法文件地址")
    algorithmIntro = Column(String(255), doc="算法描述")
    modelType = Column(String(255), nullable=False, default="yolov8", doc="算法类型")
    sdkConfig = Column(String(255), doc="SDK配置")
    createTime = Column(DateTime, nullable=False, default=datetime.now(tz), doc="创建时间")
    cameras = relationship("Camera", secondary="camera_algorithm_association", back_populates="algorithms")

    @classmethod
    def create_algorithm(cls, session: Session, name: str, modelName: str, version: str,
                         repoSource: str, camera_id: int, status: int) -> "Algorithm":
        algorithm = Algorithm(name=name, modelName=modelName, version=version, repoSource=repoSource,
                              camera_id=camera_id, status=status)
        session.add(algorithm)
        session.commit()
        session.refresh(algorithm)
        return algorithm

    @classmethod
    def get_algorithm(cls, session: Session, algorithm_id: int) -> Optional["Algorithm"]:
        return session.query(Algorithm).filter_by(id=algorithm_id).first()

    @classmethod
    def delete_algorithm(cls, session: Session, algorithm_id: int) -> bool:
        algorithm = cls.get_algorithm(session, algorithm_id)
        if algorithm:
            session.delete(algorithm)
            session.commit()
            return True
        return False

    @classmethod
    def get_camera_algorithms(cls, session: Session, camera_id: int):
        return session.query(Algorithm).filter_by(camera_id=camera_id).all()

    def update(self, session: Session, data: dict) -> None:
        for key, value in data.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)

        session.commit()
