from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from apps.database import get_db_session
from apps.models import OperateLog, Account
from apps.routers.v1.auth import get_current_user
from apps.schemas.log import OperateLogPageResponse

router = APIRouter(tags=["操作日志"])


@router.get(
    "/operate-log/page",
    response_model=OperateLogPageResponse,
    description="分页获取操作日志列表"
)
async def get_operate_log_page(
        pageNo: int = Query(1, ge=1, description="页码"),
        pageSize: int = Query(10, ge=1, le=100, description="每页显示数量"),
        session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> OperateLogPageResponse:
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    offset = (pageNo - 1) * pageSize
    operate_logs = session.query(OperateLog).offset(offset).limit(pageSize).all()
    total = session.query(OperateLog).count()

    response_data = {
        "code": 0,
        "data": {
            "list": operate_logs,
            "total": total
        },
        "msg": ""
    }

    return OperateLogPageResponse(**response_data)
