from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from apps.database import get_db_session
from apps.models import Account, Algorithm, Box
from apps.models.camera import Camera, CameraAlgorithmAssociation
from apps.routers.v1.auth import get_current_user
from apps.schemas import GeneralResponse
from apps.schemas.camera import AlgorithmInstance, CameraInfo, CameraCreate, CameraUpdateReq, AlgorithmConfig
from apps.schemas.video_task import VideoTaskConfig
from apps.services.camera import VideoTaskServer

router = APIRouter(tags=["摄像头管理"])


@router.get(
    '/cameras',
    status_code=status.HTTP_200_OK,
    description="获取所有摄像头设备信息",
)
async def get_all_cameras(
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    query = db_session.query(Camera)
    cameras = query.all()

    if not cameras:
        raise HTTPException(status_code=404, detail="No cameras found")

    camera_infos = [CameraInfo.from_orm(camera) for camera in cameras]
    total_cameras = query.count()
    online_count = query.filter(Camera.status == "在线").count()
    offline_count = query.filter(Camera.status == "离线").count()

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
    '/camera',
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="获取摄像头设备",
)
async def get_camera_info(
        camera_id: Optional[int] = None,
        camera_name: Optional[str] = None,
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="拒绝访问",
        )

    query = db_session.query(Camera)

    if camera_name:
        # 使用 like 操作符进行模糊搜索
        query = query.filter(or_(Camera.name.ilike(f'%{camera_name}%')))

    if camera_id:
        query = query.filter(Camera.camera_id == camera_id)

    cameras = query.options(joinedload(Camera.algorithms)).all()

    if not cameras:
        raise HTTPException(status_code=404, detail="摄像头未找到")

    result = []
    for camera in cameras:
        related_algorithm_instances = []
        for algorithm in camera.algorithms:
            if algorithm:
                association = db_session.query(CameraAlgorithmAssociation).filter(
                    CameraAlgorithmAssociation.algorithm_id == algorithm.id).first()

                algorithm_instance = AlgorithmInstance(
                    algorithmId=algorithm.id,
                    algorithmName=algorithm.name,
                    algorithmStatus=association.status,
                    algorithmInterval=association.frameFrequency,
                    algorithmIntro=algorithm.algorithmIntro,
                )
                related_algorithm_instances.append(algorithm_instance)

        camera_info = CameraInfo.from_orm(camera)
        camera_info.relatedAlgorithmInstances = related_algorithm_instances
        result.append(camera_info)

    return GeneralResponse(code=200, data=result, msg="摄像头信息获取成功")


@router.post(
    '/camera',
    response_model=GeneralResponse,
    status_code=status.HTTP_201_CREATED,
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

    return GeneralResponse(code=0, data=camera)


@router.put(
    '/camera/{camera_id}',
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="更新摄像头设备信息",
)
async def update_camera(
        camera_id: int,
        camera_update: CameraUpdateReq,
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
        raise HTTPException(status_code=404, detail="Camera not found")

    camera.update(db_session, camera_update.dict())
    db_session.commit()
    camera_info = CameraUpdateReq.from_orm(camera)

    return GeneralResponse(code=200, data=camera_info)


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
            data=True,
            msg=f"成功删除ID为 {camera_id} 的摄像头"
        )
    else:
        raise HTTPException(status_code=404, detail="未找到该摄像头设备")


@router.get(
    '/camera/{cameraId}/algorithm',
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="获取摄像头算法列表",
)
async def get_camera_algorithms(
        cameraId: int,
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
        algorithms = camera.algorithms

        if algorithmName:
            algorithms = [algorithm for algorithm in algorithms if algorithm.name == algorithmName]

        algorithm_data = []
        for algorithm in algorithms:
            association = session.query(CameraAlgorithmAssociation).filter(
                CameraAlgorithmAssociation.algorithm_id == algorithm.id).first()
            algorithm_data.append({
                "algorithmId": algorithm.id,
                "algorithmName": algorithm.name,
                "cameraId": camera.camera_id,
                "cameraName": camera.name,
                "status": camera.status,
                "frameFrequency": association.frameFrequency,
                "alamInterval": association.alamInterval,
                "roiValues": []
            })
        return GeneralResponse(
            code=200,
            data=algorithm_data
        )
    else:
        raise HTTPException(status_code=404, detail="Camera not found")


@router.get(
    '/camera/page',
    status_code=status.HTTP_200_OK,
    description="获取摄像头设备分页"
)
async def get_camera_page(
        page: int = 1,
        limit: int = 10,
        db_session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Access denied")

    cameras = db_session.query(Camera).limit(limit).offset((page - 1) * limit).all()

    camera_infos = []

    for camera in cameras:
        related_algorithm_instances = []
        for algorithm in camera.algorithms:
            association = db_session.query(CameraAlgorithmAssociation).filter(
                CameraAlgorithmAssociation.algorithm_id == algorithm.id,
                CameraAlgorithmAssociation.camera_id == camera.camera_id).first()
            algorithm_instance = AlgorithmInstance(
                algorithmId=algorithm.id,
                algorithmName=algorithm.name,
                algorithmStatus=association.status,
                algorithmInterval=association.frameFrequency,
                algorithmIntro=algorithm.algorithmIntro,
                sdkConfig=algorithm.sdkConfig
            )
            related_algorithm_instances.append(algorithm_instance)

        camera_info = CameraInfo.from_orm(camera)
        camera_info.relatedAlgorithmInstances = related_algorithm_instances

        camera_infos.append(camera_info)

    return {
        "code": 200,
        "data": {
            "list": camera_infos,
            "total": len(camera_infos)
        }
    }


@router.get(
    '/camera/{cameraId}/algorithm/{cameraAlgorithmId}',
    response_model=GeneralResponse,
    status_code=status.HTTP_200_OK,
    description="获取摄像头算法"
)
async def get_camera_algorithm(
        cameraId: int,
        cameraAlgorithmId: int,
        session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    algorithm = (
        session.query(Algorithm)
        .options(joinedload(Algorithm.cameras))
        .filter(Algorithm.id == cameraAlgorithmId)
        .first()
    )

    if not algorithm:
        raise HTTPException(status_code=404, detail="Camera algorithm not found")

    camera_info = None
    for camera in algorithm.cameras:
        if camera.camera_id == cameraId:
            camera_info = CameraInfo.from_orm(camera)
            break

    if not camera_info:
        raise HTTPException(status_code=404, detail="Camera not found")

    association = session.query(CameraAlgorithmAssociation).filter(
        CameraAlgorithmAssociation.algorithm_id == cameraAlgorithmId,
        CameraAlgorithmAssociation.camera_id == cameraId
    ).first()

    algorithm_data = {
        "algorithmId": algorithm.id,
        "algorithmName": algorithm.name,
        "cameraId": camera_info.camera_id,
        "cameraName": camera_info.name,
        "status": camera_info.status,
        "frameFrequency": association.frameFrequency,
        "alamInterval": association.alamInterval,
        "sdkConfig": algorithm.sdkConfig,
        "roiValues": ''
    }

    return GeneralResponse(code=0, data=algorithm_data, msg="")


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
        raise HTTPException(status_code=404, detail="算法未找到")

    association_exists = (
        session.query(CameraAlgorithmAssociation)
        .filter_by(camera_id=cameraId, algorithm_id=algorithm.id)
        .first()
    )

    if association_exists:
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
        interval=association_exists.frameFrequency,
        model_type=algorithm.modelType,
        return_url=box.return_url
    )

    if algorithm_config.status:
        video_task_server = VideoTaskServer()
        video_task_server.start(config)

    return GeneralResponse(
        code=200,
        data=None,
        msg="摄像头算法配置已保存"
    )


@router.post(
    "/camera/return",
    description="告警回传地址配置"
)
async def save_camera_return_url(
        return_url: str,
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
    session.commit()
    return GeneralResponse(
        code=200,
        msg="保存成功！"
    )
