import os
from typing import List

from fastapi import APIRouter, UploadFile, File, status, Depends, Query, HTTPException, Form
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette import status

from apps.database import get_db_session
from apps.models import Algorithm, Account
from apps.routers.v1.auth import get_current_user
from apps.schemas import GeneralResponse
from apps.schemas.algorithm import PageResultAlgorithmInfoResp, AlgorithmInfoResp

router = APIRouter(tags=["算法管理"])


@router.post(
    "/algorithm/uploadAlgorithmFile",
    response_model=None,
    status_code=status.HTTP_200_OK,
    description="算法文件上传",
)
async def upload_algorithm_file(
        file: UploadFile = File(...),
        path: str = Form(None),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    # 处理上传的文件
    contents = file.file.read()
    if path is None:
        # 将文件保存到指定路径
        with open(f"apps/detection/models/{file.filename}", "wb") as f:
            f.write(contents)
    else:
        os.makedirs(path, exist_ok=True)
        with open(f"apps/detection/models/{path}/{file.filename}", "wb") as f:
            f.write(contents)

    return GeneralResponse(
        code=200,
        msg="文件上传成功"
    )


@router.get(
    "/algorithm/page",
    response_model=PageResultAlgorithmInfoResp,
    description="获取算法信息分页"
)
async def get_paged_algorithm_info(
        page_no: int = Query(..., gt=0),
        page_size: int = Query(..., gt=0, le=100),
        name: str = Query(None),
        session: Session = Depends(get_db_session),
) -> PageResultAlgorithmInfoResp:
    # 查询算法信息
    query = session.query(Algorithm)
    if name:
        query = query.filter(Algorithm.name == name)

    total = query.count()

    algorithms = query.offset((page_no - 1) * page_size).limit(page_size).all()

    algorithm_list = [
        AlgorithmInfoResp(
            name=algo.name,
            modelName=algo.modelName,
            version=algo.version,
            repoSource=algo.repoSource,
            id=algo.id,
            createTime=str(algo.createTime)
        )
        for algo in algorithms
    ]

    return PageResultAlgorithmInfoResp(
        list=algorithm_list,
        total=total
    )


@router.get(
    "/algorithm/list",
    response_model=List[AlgorithmInfoResp],
    description="展示所有算法信息的列表"
)
async def get_algorithm_list(
        name: str = Query(None, description="算法名称"),
        session: Session = Depends(get_db_session),
) -> List[AlgorithmInfoResp]:
    # 查询算法信息
    query = session.query(Algorithm)
    if name:
        query = query.filter(Algorithm.name == name)

    algorithms = query.all()

    algorithm_list = [
        AlgorithmInfoResp(
            name=algo.name,
            modelName=algo.modelName,
            version=algo.version,
            repoSource=algo.repoSource,
            id=algo.id,
            createTime=str(algo.createTime)
        )
        for algo in algorithms
    ]

    return algorithm_list


@router.delete(
    "/algorithm/delete",
    response_model=GeneralResponse,
    description="删除算法模型文件"
)
async def delete_algorithm_file(
        algo_id: int = Query(..., description="算法模型文件的ID"),
        session: Session = Depends(get_db_session),
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )
    # 查询算法模型文件信息
    algorithm = session.query(Algorithm).get(algo_id)

    if not algorithm:
        return GeneralResponse(code=1, msg="未找到对应的算法模型文件")

    # 删除数据库中的算法模型文件信息
    session.delete(algorithm)
    session.commit()

    # 删除对应路径下的文件
    file_path = algorithm.repoSource
    if os.path.exists(file_path):
        os.remove(file_path)
        return GeneralResponse(code=0, msg="算法模型文件删除成功")
    else:
        return GeneralResponse(code=1, msg="文件不存在")


@router.get(
    "/algorithms",
    response_model=GeneralResponse,  # 请根据实际情况调整返回的数据模型
    description="算法搜索",
)
def search_algorithm_by_name(
        name: str,
        session: Session = Depends(get_db_session),
):
    algorithms = session.query(Algorithm).filter(Algorithm.name.ilike(f"%{name}%")).all()

    if not algorithms:
        raise HTTPException(status_code=404, detail="No algorithms found with the given name")

    return GeneralResponse(
        code=200,
        data=algorithms
    )


@router.get(
    "/algorithms/stats",
    description="按算法状态统计",
)
def get_algorithm_stats(
        current_user: Account = Depends(get_current_user),
        db_session: Session = Depends(get_db_session),
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    stats = (
        db_session.query(Algorithm.status, func.count().label('count'))
        .group_by(Algorithm.status)
        .all()
    )

    return {
        "code": 200,
        "data": [{"status": status, "count": count} for status, count in stats]
    }
