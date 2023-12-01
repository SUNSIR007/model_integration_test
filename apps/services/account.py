from typing import Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from apps.config import settings
from apps.models.account import Account
from apps.schemas import get_error_response, GeneralResponse
from apps.schemas.account import AccountCreateSchema, AccountUpdateSchema, AccountChangePasswordSchema

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_account_by_name(username: str, db_session: Session) -> Optional[Account]:
    query = db_session.query(Account)
    if username:
        query = query.filter(Account.username == username)
        if query.first():
            return query.first()
    return None


def get_account_by_email(email: str, db_session: Session) -> Optional[Account]:
    query = db_session.query(Account)
    if email:
        query = query.filter(Account.email == email)
        if query.first():
            return query.first()
    return None


async def create(payload: AccountCreateSchema, db_session: Session):
    if get_account_by_name(payload.username, db_session):
        return get_error_response(400101)
    if get_account_by_email(payload.email, db_session):
        return get_error_response(400101)

    # Database only store the hashed password.
    encrypted_password = password_context.hash(settings.password)
    account = Account(
        username=payload.username,
        encrypted_password=encrypted_password,
        email=payload.email,
        phone=payload.phone,
        is_active=payload.is_active,
    )

    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    return GeneralResponse(code=0, data=account)


async def update(
        account_id: int,
        payload: AccountUpdateSchema,
        db_session: Session,
):
    account = Account.get_object_by_id(account_id, db_session)
    if not account:
        return get_error_response(400118)

    # 如果修改用户名，需要确认用户名是否重复
    if account.username != payload.username:
        exist_account = get_account_by_name(
            payload.username,
            db_session,
        )
        if exist_account and exist_account.id != account.id:
            return get_error_response(400101)
    # 如果修改邮箱，需要确认邮箱是否重复
    if account.email != payload.email:
        exist_account = get_account_by_email(
            payload.email,
            db_session,
        )
        if exist_account and exist_account.id != account.id:
            return get_error_response(400101)

    # update account below
    if payload.username is not None:
        account.username = payload.username

    if payload.email is not None:
        account.email = payload.email

    if payload.phone is not None:
        account.phone = payload.phone

    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    return GeneralResponse(code=0, data=account)


def verify_password(plain_password: str, hashed_password: str):
    return password_context.verify(plain_password, hashed_password)


async def change_account_password(
    accoount_id: int,
    payload: AccountChangePasswordSchema,
    session: Session,
):
    if payload.newpassword != payload.repassword:
        return get_error_response(400119)

    account = Account.get_object_by_id(accoount_id, session)
    if not account:
        return get_error_response(400118)

    if not verify_password(payload.password, account.encrypted_password):
        return get_error_response(400200)

    account.encrypted_password = password_context.hash(payload.newpassword)

    session.add(account)
    session.commit()
    session.refresh(account)

    return GeneralResponse(code=0, data="OK")


async def entry(
    offset: int,
    limit: int,
    db_session: Session,
):
    query = (
        db_session.query(Account)
        .filter(Account.deleted_at.is_(None))
    )

    query = query.order_by(Account.id.desc())
    total = query.count()
    items = query.offset(offset * limit).limit(limit).all()

    data = {
        "total": total,
        "items": items,
    }
    return GeneralResponse(code=0, data=data)


async def delete(account_id: int, session: Session):
    account = Account.get_object_by_id(account_id, session)
    if not account:
        return get_error_response(400118)

    # soft delete
    session.delete(account)
    session.commit()

    return GeneralResponse(code=0, data=account)
