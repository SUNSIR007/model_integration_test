from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Float
from sqlalchemy.orm import Session

from apps.database import Base


class Box(Base):
    __tablename__ = "box"
    id = Column(Integer, primary_key=True, autoincrement=True, doc='设备编号')
    system_name = Column(String(32), nullable=False, doc='系统名称')
    timezone = Column(String(32), nullable=False, doc='时区')
    ip_address = Column(String(32), nullable=False, doc='IP地址')
    port = Column(Integer, doc='设备端口')
    return_url = Column(String(255), doc='结果回传地址')
    return_token = Column(String(255), doc='回传地址bear token')
    device_name = Column(String(32), nullable=False, doc='设备名称')
    device_number = Column(String(32), nullable=False, doc='设备编号')
    hardware_version = Column(String(32), nullable=False, doc='硬件版本')
    web_version = Column(String(32), nullable=False, doc='Web版本')
    software_version = Column(String(32), nullable=False, doc='软件版本')

    @classmethod
    def query(cls, session: Session):
        return session.query(cls)

    @classmethod
    def get_object_by_id(cls, obj_id: int, session: Session):
        return cls.query(session).filter(cls.id == obj_id).first()
