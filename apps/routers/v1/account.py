from fastapi import APIRouter, Depends, status, Body, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from apps.database import get_db_session
from apps.models import Account
from apps.routers.v1.auth import get_current_user
from apps.schemas import GeneralResponse
from apps.schemas.account import AccountCreateSchema, AccountChangePasswordSchema, AccountUpdateSchema
from apps.services.account import (
    change_account_password,
    create,
    update,
    entry,
    delete
)

router = APIRouter(tags=["用户管理"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post(
    "/system/user",
    response_model=GeneralResponse,
    status_code=status.HTTP_201_CREATED,
    description="创建账户",
)
async def create_account(
        account: AccountCreateSchema,
        db_session: Session = Depends(get_db_session),
):
    return await create(account, db_session)


@router.get(
    "/system/user",
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="账户列表",
)
async def get_accounts(
        offset: int = 0,
        limit: int = 10,
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
):
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=400,
            detail=f"用户权限不足"
        )
    return await entry(offset, limit, db_session)


@router.delete(
    "/system/user",
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="账户删除",
)
async def delete_account(
        id: int = Body(..., embed=True),
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
):
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=400,
            detail=f"用户权限不足"
        )
    return await delete(id, db_session)


@router.put(
    "/system/user/password",
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="修改账号密码",
)
async def change_password(
        payload: AccountChangePasswordSchema,
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
):
    account_id = current_user.id
    return await change_account_password(account_id, payload, db_session)


@router.put(
    "/system/user",
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="账户更新",
)
async def update_account(
        payload: AccountUpdateSchema,
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
):
    account_id = current_user.id
    return await update(account_id, payload, db_session)
