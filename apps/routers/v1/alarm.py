from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from starlette import status

from apps.database import get_db_session
from apps.models import Account, Alarm
from apps.routers.v1.auth import get_current_user
from apps.schemas import GeneralResponse
from apps.schemas.alarm import AlarmRecordCreateReq, UpdateAlarmRecordRequest, AlarmFilterParams

router = APIRouter(tags=["告警管理"])


@router.post(
    '/alarms',
    status_code=status.HTTP_200_OK,
    description="创建告警记录",
)
async def create_alarm(
        alarm_data: AlarmRecordCreateReq,
        current_user: Account = Depends(get_current_user),
        db_session: Session = Depends(get_db_session),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    alarm = Alarm(**alarm_data.dict())

    db_session.add(alarm)
    db_session.commit()

    return GeneralResponse(
        code=200,
        meg="告警记录创建成功！"
    )


@router.put(
    "/alarms",
    description="更新告警记录",
)
def update_alarm_record(
        request_data: UpdateAlarmRecordRequest,
        current_user: Account = Depends(get_current_user),
        db_session: Session = Depends(get_db_session),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    alarm = db_session.query(Alarm).get(request_data.id)
    if not alarm:
        return {"message": "Alarm record not found"}

    alarm.update(db_session, request_data.dict(exclude={"id"}))

    return {"message": "Alarm record updated successfully"}


@router.get(
    "/alarms/{alarm_id}",
    description="查询告警记录",
)
def get_alarm_record(
        alarm_id: int,
        current_user: Account = Depends(get_current_user),
        db_session: Session = Depends(get_db_session),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    # 查询告警记录
    alarm = db_session.query(Alarm).get(alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm record not found")

    return GeneralResponse(
        code=200,
        data=alarm
    )


@router.delete(
    "/alarms/{alarm_id}",
    description="删除告警记录",
)
def delete_alarm_record(
        alarm_id: int,
        current_user: Account = Depends(get_current_user),
        db_session: Session = Depends(get_db_session),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    # 查询要删除的告警记录
    alarm = db_session.query(Alarm).get(alarm_id)
    if not alarm:
        raise HTTPException(
            status_code=404,
            detail="Alarm record not found",
        )

    # 删除告警记录
    db_session.delete(alarm)
    db_session.commit()

    return GeneralResponse(
        code=200,
        meg="Alarm record deleted successfully!"
    )


@router.get(
    "/alarms",
    description="告警记录分页",
)
def get_alarm_records_page(
        current_user: Account = Depends(get_current_user),
        db_session: Session = Depends(get_db_session),
        page_no: int = Query(..., gt=0),
        page_size: int = Query(..., gt=0, le=100),
        filter_params: AlarmFilterParams = Depends(),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    conditions = []
    for key, value in filter_params.dict(exclude_unset=True).items():
        if value is not None:
            conditions.append(getattr(Alarm, key).ilike(f"%{value}%"))

    query = db_session.query(Alarm).filter(or_(*conditions))
    total_count = query.count()
    alarm_records = query.offset((page_no - 1) * page_size).limit(page_size).all()

    return {
        "code": 200,
        "data": {
            "list": alarm_records,
            "total": total_count,
        }
    }
