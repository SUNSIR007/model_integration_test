from typing import Optional

import cv2
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload

from apps.database import get_db_session
from apps.models import Account, Algorithm, Box
from apps.models.camera import Camera, CameraAlgorithmAssociation
from apps.routers.v1.auth import get_current_user
from apps.schemas import GeneralResponse
from apps.schemas.camera import CameraInfo, CameraCreate, AlgorithmConfig
from apps.schemas.video_task import VideoTaskConfig
from apps.services.camera import VideoTaskServer
from apps.worker.celery_worker import screenshot

router = APIRouter(tags=["摄像头管理"])


@router.post(
    '/camera',
    description="创建摄像头",
)
async def create_camera(
        camera_create: CameraCreate,
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    camera = Camera(**camera_create.dict())

    db_session.add(camera)
    db_session.commit()
    db_session.refresh(camera)

    return GeneralResponse(code=200, msg="Camera created successfully.")


@router.delete(
    '/camera',
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="删除摄像头设备",
)
async def delete_camera(
        camera_id: int,
        session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    camera = session.query(Camera).get(camera_id)
    if camera:
        camera.delete(session)
        return GeneralResponse(
            code=200,
            msg=f"Camera deleted successfully."
        )
    else:
        raise HTTPException(status_code=404, detail="Camera not found.")


@router.put(
    '/camera/{camera_id}',
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="更新摄像头设备信息",
)
async def update_camera(
        camera_id: int,
        camera_update: CameraInfo,
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    camera = db_session.query(Camera).get(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found.")

    camera.update(db_session, camera_update.dict())
    db_session.commit()
    camera_info = CameraInfo.from_orm(camera)

    return GeneralResponse(code=200, data=camera_info)


@router.get(
    '/camera',
    status_code=status.HTTP_200_OK,
    description="获取摄像头设备信息",
)
async def get_camera(
        camera_id: Optional[int] = None,
        camera_name: Optional[str] = None,
        page_no: int = Query(1, gt=0),
        page_size: int = Query(10, gt=0, le=100),
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    query = db_session.query(Camera)

    if camera_name:
        query = query.filter(or_(Camera.name.ilike(f'%{camera_name}%')))

    if camera_id:
        query = query.filter(Camera.camera_id == camera_id)

    total_cameras = query.count()

    cameras = query.offset((page_no - 1) * page_size).limit(page_size).all()

    if not cameras:
        raise HTTPException(status_code=404, detail="Camera not found")

    camera_infos = [CameraInfo.from_orm(camera) for camera in cameras]

    online_count = query.filter(Camera.status == 1).count()
    offline_count = query.filter(Camera.status == 0).count()

    return GeneralResponse(
        code=200,
        data={
            "camera_infos": camera_infos,
            "total_cameras": total_cameras,
            "online_count": online_count,
            "offline_count": offline_count
        }
    )


@router.get(
    '/camera/{cameraId}/algorithm',
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="获取摄像头算法",
)
async def get_camera_algorithms(
        cameraId: int,
        cameraAlgorithmId: Optional[str] = None,
        algorithmName: Optional[str] = None,
        session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    camera = session.query(Camera).options(joinedload(Camera.algorithms)).get(cameraId)

    if camera:
        algorithms_query = session.query(Algorithm).filter(
            Algorithm.id.in_([algorithm.id for algorithm in camera.algorithms]))

        if cameraAlgorithmId:
            algorithms_query = algorithms_query.filter(Algorithm.id == cameraAlgorithmId)

        if algorithmName:
            algorithms_query = algorithms_query.filter(func.lower(Algorithm.name).ilike(f'%{algorithmName.lower()}%'))

        algorithms = algorithms_query.all()

        algorithm_data = []
        for algorithm in algorithms:
            association = session.query(CameraAlgorithmAssociation).filter(
                CameraAlgorithmAssociation.algorithm_id == algorithm.id,
                CameraAlgorithmAssociation.camera_id == cameraId).first()
            algorithm_data.append({
                "algorithmId": algorithm.id,
                "algorithmName": algorithm.name,
                "cameraId": camera.camera_id,
                "cameraName": camera.name,
                "status": association.status,
                "frameFrequency": association.frameFrequency,
                "alamInterval": association.alamInterval,
                "conf": association.conf,
                "startHour": association.startHour,
                "startMinute": association.startMinute,
                "endHour": association.endHour,
                "endMinute": association.endMinute
            })
        return GeneralResponse(
            code=200,
            data=algorithm_data
        )
    else:
        raise HTTPException(status_code=404, detail="Camera not found")


@router.post(
    "/camera/{cameraId}/algorithm",
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="保存摄像头算法配置"
)
async def save_camera_algorithm_config(
        cameraId: int,
        algorithm_config: AlgorithmConfig,
        session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    algorithm = session.query(Algorithm).filter_by(id=algorithm_config.algorithmId).first()
    camera = session.query(Camera).filter_by(camera_id=cameraId).first()

    if not algorithm:
        raise HTTPException(status_code=404, detail="Algorithm not found.")

    association_exists = (
        session.query(CameraAlgorithmAssociation)
        .filter_by(camera_id=cameraId, algorithm_id=algorithm.id)
        .first()
    )
    original_status = None
    if association_exists:
        original_status = association_exists.status
        association_exists.update(session, algorithm_config.dict())
    else:
        association = CameraAlgorithmAssociation(camera_id=cameraId, algorithm_id=algorithm.id)
        session.add(association)
        session.commit()

    box = session.query(Box).first()
    if not box:
        raise HTTPException(status_code=404, detail="Device not found")

    config = VideoTaskConfig(
        alarm_name=algorithm.name,
        model_name=algorithm.modelName,
        camera_id=cameraId,
        algorithm_id=algorithm.id,
        video_stream_url=camera.get_video_stream_url(),
        model_type=algorithm.modelType
    )

    if algorithm_config.status and not original_status:
        video_task_server = VideoTaskServer()
        video_task_server.start(config)

    return GeneralResponse(
        code=200,
        msg="Camera algorithm configuration saved."
    )


@router.delete(
    "/camera/{cameraId}/algorithm/{algorithm_id}",
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="删除摄像头算法"
)
async def delete_camera_algorithm_config(
        cameraId: int,
        algorithm_id: int,
        session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    association_exists = (
        session.query(CameraAlgorithmAssociation)
        .filter_by(camera_id=cameraId, algorithm_id=algorithm_id)
        .first()
    )
    if association_exists:
        session.delete(association_exists)
        session.commit()
        return GeneralResponse(
            code=200,
            msg=f"Camera Algorithm config deleted successfully."
        )
    else:
        raise HTTPException(status_code=404, detail="Camera Algorithm config not found.")


@router.post(
    "/camera/return",
    description="告警回传地址配置"
)
async def save_camera_return_url(
        return_url: str,
        access_token: Optional[str] = None,
        session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    box = session.query(Box).first()
    if not box:
        raise HTTPException(status_code=404, detail="Device not found")
    box.return_url = return_url
    box.return_token = access_token
    session.commit()
    return GeneralResponse(
        code=200,
        msg="Alarm return address saved successfully."
    )


@router.post(
    "/camera/snapshot",
    description="获取摄像头当前帧"
)
async def get_current_frame(
        camera_id: int,
        session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    camera = session.query(Camera).filter(Camera.camera_id == camera_id).first()
    video_url = camera.get_video_stream_url()
    frame = screenshot(video_url)
    filepath = 'static/snapshot/'
    if frame is not None:
        cv2.imwrite(f'{filepath}{camera_id}.jpg', frame)

        return GeneralResponse(
            code=200,
            data={
                "snapshot_path": f'{filepath}{camera_id}.jpg'
            }
        )
    else:
        return GeneralResponse(
            code=200,
            msg="Please check the video stream address."
        )
