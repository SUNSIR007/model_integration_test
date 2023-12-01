from typing import List, Optional

from pydantic import BaseModel


class AccountBase(BaseModel):
    username: str
    email: str
    phone: str


class AccountCreateSchema(AccountBase):
    is_active: Optional[bool] = True


class AccountUpdateSchema(BaseModel):
    username: Optional[str]
    email: Optional[str]
    phone: Optional[str]


class AccountDeleteSchema(BaseModel):
    account_ids: Optional[List[int]] = []


class AccountSchema(AccountBase):
    password: str
    is_active: Optional[bool] = True

    class Config:
        orm_mode = True


class AccountChangePasswordSchema(BaseModel):
    password: Optional[str]
    newpassword: Optional[str]
    repassword: Optional[str]
