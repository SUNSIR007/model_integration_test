from datetime import timedelta, datetime
from typing import Union

from fastapi import APIRouter, Body, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from apps.config import settings
from apps.database import get_db_session
from apps.models import Account
from apps.schemas import GeneralResponse

jwt_auth_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
)

router = APIRouter(tags=["认证"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str):
    """密码验证"""
    return password_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Union[timedelta, int]):
    """创建令牌"""
    # 复制输入的数据并获取当前时间
    jwt_payload, now = data.copy(), datetime.utcnow()

    if isinstance(expires_delta, int):
        expires_delta = timedelta(seconds=expires_delta)

    # 计算令牌的过期时间
    expired = now + expires_delta
    # 更新令牌时间
    jwt_payload.update({"exp": expired})

    access_token = jwt.encode(
        jwt_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return access_token


def authenticate(db_session: Session, username: str, password: str):
    """身份验证"""
    account = Account.get_object_by_username(username, db_session)
    if not account:
        return False

    if not verify_password(password, account.encrypted_password):
        return False

    return account


def get_current_user(token: str = Depends(oauth2_scheme), db_session: Session = Depends(get_db_session)):
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        # 根据需要从数据库获取用户信息并返回
        user = Account.get_object_by_username(username, db_session)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.post(
    '/system/auth/login',
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="系统登录",
)
async def login_for_access_token(
        username: str = Body(...),
        password: str = Body(...),
        db_session: Session = Depends(get_db_session),
) -> GeneralResponse:
    account = authenticate(db_session, username, password)
    if not account:
        return GeneralResponse(code=400100, msg="Incorrect username or password")
    if account.is_active is not True:
        return GeneralResponse(code=400101, msg="account is disabled")

    access_token = create_access_token(
        data={"sub": account.username},
        expires_delta=settings.jwt_access_token_expire_seconds
    )

    expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)
    refresh_token = create_access_token(
        data={"sub": account.username},
        expires_delta=expires_delta
    )

    # 保存令牌到数据库
    account.token = access_token
    account.refresh_token = refresh_token
    db_session.add(account)
    db_session.commit()

    expires_time = datetime.now() + expires_delta

    return GeneralResponse(
        code=200,
        data={
            "userId": account.id,
            "accessToken": access_token,
            "tokenType": "bearer",
            "refreshToken": refresh_token,
            "expiresTime": expires_time
        }
    )


@router.post(
    '/system/auth/logout',
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="系统登出",
)
async def logout(
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    return GeneralResponse(code=200, msg=f"User {current_user.username} logged out successfully.")


@router.put(
    '/system/auth/refresh-token',
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="刷新令牌",
)
async def refresh_token(
        refresh_token: str,
        db_session: Session = Depends(get_db_session)
) -> GeneralResponse:
    account = db_session.query(Account).filter(Account.refresh_token == refresh_token).first()
    if not account:
        return GeneralResponse(code=400, msg="Token not found")

    expires_delta = timedelta(days=settings.jwt_refresh_token_expire_days)
    new_refresh_token = create_access_token(
        data={"sub": account.username},
        expires_delta=expires_delta,
    )

    # 更新令牌字段
    account.token = new_refresh_token
    db_session.add(account)
    db_session.commit()

    expires_time = datetime.now() + expires_delta

    return GeneralResponse(
        code=200,
        data={
            "userId": account.id,
            "accessToken": account.token,
            "refreshToken": refresh_token,
            "tokenType": "bearer",
            "expiresTime": expires_time,
        }
    )


@router.get(
    '/system/auth/permissions',
    status_code=status.HTTP_200_OK,
    description="获取用户权限",
)
async def get_user_permissions(
        current_user: Account = Depends(get_current_user),
        db_session: Session = Depends(get_db_session),
) -> GeneralResponse:
    account = db_session.query(Account).filter(Account.id == current_user.id).first()
    if not account:
        return GeneralResponse(code=400, msg="Account not found")
    return GeneralResponse(
        code=200,
        data={
            "user": {
                "id": account.id,
                "nickname": account.username,
                "avatar": ""
            }
        }
    )
