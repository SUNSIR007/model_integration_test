from datetime import datetime
from typing import Optional

import pytz
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.orm import Session
from typing_extensions import Self

from apps.database import Base

tz = pytz.timezone('Asia/Shanghai')


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, autoincrement=True, doc='用户编号')
    username = Column(String(32), nullable=False, doc='用户名')
    encrypted_password = Column(String(64), nullable=False, doc='密码')
    email = Column(String(32), index=True, nullable=False, doc='邮箱')
    phone = Column(String(32), index=True, nullable=False, doc='电话')
    role = Column(String(32), nullable=False, default='普通用户', doc='用户角色')
    is_active = Column(Boolean, nullable=False, doc='账户启用状态')
    token = Column(String(255), nullable=True, doc='用户令牌')
    refresh_token = Column(String(255), nullable=True, doc='刷新令牌')
    created_at = Column(DateTime, nullable=False, default=datetime.now(tz), doc='创建时间')
    updated_at = Column(DateTime, nullable=False, default=datetime.now(tz), doc='更新时间')
    deleted_at = Column(DateTime, nullable=True, doc='是否删除')

    @classmethod
    def query(cls, session: Session):
        return session.query(cls).filter(cls.deleted_at.is_(None))

    @classmethod
    def get_object_by_username(
            cls,
            username: str,
            session: Session,
    ) -> Optional[Self]:
        return cls.query(session).filter(cls.username == username).first()

    @classmethod
    def get_object_by_id(cls, obj_id: int, session: Session) -> Optional[Self]:
        return cls.query(session).filter(cls.id == obj_id).first()

    @classmethod
    def get_user_by_token(cls, token: str, session: Session) -> Optional[Self]:
        return cls.query(session).filter(cls.token == token).first()
