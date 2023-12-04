from datetime import datetime
from subprocess import run

import pytz
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from apps.database import get_db_session
from apps.models import Account
from apps.models.box import Box
from apps.routers.v1.auth import get_current_user
from apps.schemas import GeneralResponse
from apps.schemas.box import UpdateSystemNameRequest, UpdateTimeRequest, UpdateIpRequest
from apps.utils.box import get_memory_total, get_memory_usage, get_disk_total, get_disk_usage, get_temperature, \
    get_cpu_usage

router = APIRouter(tags=["盒子管理"])


@router.put(
    '/box/systemName',
    response_model=None,
    status_code=status.HTTP_200_OK,
    description="更新系统名称",
)
async def update_system_name(
        request: UpdateSystemNameRequest,
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    box = db_session.query(Box).first()
    if not box:
        raise HTTPException(status_code=404, detail="box not found")

    box.system_name = request.system_name
    db_session.commit()
    return GeneralResponse(
        code=200,
        data=True
    )


@router.put(
    '/box/time',
    response_model=None,
    status_code=status.HTTP_200_OK,
    description="更新系统时间",
)
async def update_system_time(
        request: UpdateTimeRequest,
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    box = db_session.query(Box).first()
    if not box:
        raise HTTPException(status_code=404, detail="Server not found")

    # 更新系统时间和时区
    box.time = datetime.now(request.date.tzinfo)
    box.timezone = request.timeZone

    db_session.commit()

    return GeneralResponse(
        code=200,
        data=True
    )


@router.put(
    '/box/ip',
    response_model=None,
    status_code=status.HTTP_200_OK,
    description="更新IP地址",
)
async def update_ip_address(
        request: UpdateIpRequest,
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    box = db_session.query(Box).first()
    if not box:
        raise HTTPException(status_code=404, detail="Server not found")

    box.ip_address = request.ip_address
    db_session.commit()
    return GeneralResponse(
        code=200,
        data={},
        msg="更新成功！"
    )


@router.post(
    '/box/reset',
    response_model=None,
    status_code=status.HTTP_200_OK,
    description="系统重置",
)
async def reset_system(
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    return GeneralResponse(
        code=200,
        data=True
    )


@router.post(
    '/box/reboot',
    response_model=None,
    status_code=status.HTTP_200_OK,
    description="重启系统",
)
async def reboot_system(
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    # 执行重启系统命令
    run(['reboot'])
    return GeneralResponse(
        code=200,
        data=True,
        msg="系统已重启"
    )


@router.delete(
    '/box',
    response_model=None,
    status_code=status.HTTP_200_OK,
    description="清空数据",
)
async def delete_data(
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> None:
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    # 删除所有服务器实例
    db_session.query(Box).delete()
    db_session.commit()


@router.get(
    '/box/time',
    response_model=dict,
    status_code=status.HTTP_200_OK,
    description="获取系统时间",
)
async def get_system_time() -> GeneralResponse:
    # 获取当前时间和时区
    current_time = datetime.now()
    timezone = pytz.timezone("Asia/Shanghai")
    localized_time = timezone.localize(current_time)

    # 构造返回数据字典
    data = {
        "timeZone": timezone.zone,
        "time": localized_time.strftime("%Y-%m-%d %H:%M:%S")
    }

    return GeneralResponse(
        code=200,
        data=data
    )


@router.get(
    '/box',
    response_model=dict,
    status_code=status.HTTP_200_OK,
    description="获取设备信息",
)
async def get_device_info(
        db_session: Session = Depends(get_db_session),
) -> GeneralResponse:
    box = db_session.query(Box).first()
    if not box:
        raise HTTPException(status_code=404, detail="Device not found")

    return GeneralResponse(
        code=200,
        data={
            "name": box.system_name,
            "id": box.id,
            "hardwareVersion": box.hardware_version,
            "firmwareVersion": box.hardware_version,
            "webVersion": box.web_version,
            "softwareVersion": box.software_version,
            "ip": box.ip_address
        }
    )


@router.get(
    '/box/SystemInfo',
    response_model=dict,
    status_code=status.HTTP_200_OK,
    description="获取系统资源信息",
)
async def get_system_info() -> GeneralResponse:
    # 获取系统资源信息
    memory_total = get_memory_total()
    memory_usage = get_memory_usage()
    disk_total = get_disk_total()
    disk_usage = get_disk_usage()
    # temperature = get_temperature()
    cpu_usage = get_cpu_usage()

    # 构造返回数据字典
    data = {
        "memoryTotal": memory_total,
        "memoryUsage": memory_usage,
        "diskTotal": disk_total,
        "diskUsage": disk_usage,
        "temperature": 0,
        "cpuusage": cpu_usage
    }

    return GeneralResponse(
        code=200,
        data=data
    )