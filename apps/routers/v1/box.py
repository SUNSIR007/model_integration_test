import os
from datetime import datetime
from subprocess import run
import re
import pytz
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from apps.database import get_db_session
from apps.models import Account
from apps.models.box import Box
from apps.routers.v1.auth import get_current_user
from apps.schemas import GeneralResponse
from apps.schemas.box import UpdateSystemNameRequest, UpdateTimeRequest, UpdateConfig, CleanSpace
from apps.utils.box import get_memory_total, get_memory_usage, get_disk_total, get_disk_usage, get_temperature, \
    get_cpu_usage

router = APIRouter(tags=["盒子管理"])
fronted_path = '../dist/webconfig.js'
run_path = 'backup.sh'


def read_config(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            config_content = f.read()
        return config_content
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Config file not found")


def write_config(config_content, path):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(config_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config: {str(e)}")


def update_shell_script(ip, port):
    sh_content = read_config(run_path)
    pattern = r'--host (\d{1,3}\.){3}\d{1,3} --port \d{4}'
    replacement = rf'--host {ip} --port {port}'
    updated_run_content = re.sub(pattern, replacement, sh_content)
    write_config(updated_run_content, run_path)


def update_js_config(ip, port):
    js_content = read_config(fronted_path)
    new_web_api_base_url = f'http://{ip}:{port}'
    pattern = r'(webConfig = {\n\s*"webApiBaseUrl": ")(.*?)(",\n\s*"webSystemTitle)'
    replacement = rf'\1{new_web_api_base_url}\3'
    updated_js_content = re.sub(pattern, replacement, js_content)
    write_config(updated_js_content, fronted_path)


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
    '/box/config',
    response_model=None,
    status_code=status.HTTP_200_OK,
    description="更新IP和端口",
)
async def update_ip_address(
        config: UpdateConfig,
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    ip, port = config.ip, config.port

    box = db_session.query(Box).first()
    if not box:
        raise HTTPException(status_code=404, detail="Server not found")
    if not ip or not port:
        raise HTTPException(status_code=422, detail="Missing required query parameter: query_param")

    box.ip_address, box.port = ip, port
    db_session.commit()

    # 更新前端配置文件
    update_js_config(ip, port)
    # 更新后端启动脚本
    update_shell_script(ip, port)

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

    if os.path.exists('./model_integration.db'):
        os.remove('./model_integration.db')
    if os.path.exists('static/data'):
        os.remove('static/data')

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
            "device_name": box.device_name,
            "device_number": box.device_number,
            "hardwareVersion": box.hardware_version,
            "webVersion": box.web_version,
            "softwareVersion": box.software_version,
            "ip": box.ip_address,
            "port": box.port,
            "storage_period": box.storage_period,
            "storage_threshold": box.storage_threshold
        }
    )


@router.get(
    '/box/SystemInfo',
    status_code=status.HTTP_200_OK,
    description="获取系统资源信息",
)
async def get_system_info() -> GeneralResponse:
    # 获取系统资源信息
    memory_total = get_memory_total()
    memory_usage = get_memory_usage()
    disk_total = get_disk_total()
    disk_usage = get_disk_usage()
    temperature = get_temperature()
    cpu_usage = get_cpu_usage()

    # 构造返回数据字典
    data = {
        "memoryTotal": memory_total,
        "memoryUsage": memory_usage,
        "diskTotal": disk_total,
        "diskUsage": disk_usage,
        "temperature": temperature,
        "cpuusage": cpu_usage
    }

    return GeneralResponse(
        code=200,
        data=data
    )


@router.post(
    '/box/cleanSpace',
    status_code=status.HTTP_200_OK,
    description="磁盘清理配置",
)
async def clean_space(
        cleanConfig: CleanSpace,
        current_user: Account = Depends(get_current_user),
        db_session: Session = Depends(get_db_session)
) -> GeneralResponse:
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    box = db_session.query(Box).first()
    if not box:
        raise HTTPException(status_code=404, detail="Server not found")
    box.storage_period, box.storage_threshold = cleanConfig.storagePeriod, cleanConfig.storageThreshold
    db_session.commit()

    return GeneralResponse(
        code=200,
        msg="配置保存成功"
    )
