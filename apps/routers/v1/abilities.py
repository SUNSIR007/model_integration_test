import base64

from fastapi import APIRouter, HTTPException, Depends

from apps.models import Account
from apps.routers.v1.auth import get_current_user
from apps.schemas.abilities import VideoTaskSchame, AnalyseResultSchema
from apps.services.abilities import VideoTaskServer

router = APIRouter(tags=["视频任务管理"])


@router.post(
    "/service/videoTask",
    description="视频任务管理",
)
async def video_task(
        task: VideoTaskSchame,
        current_user: Account = Depends(get_current_user),
):
    # 检查用户是否具有特定权限
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    video_task = VideoTaskServer(task)

    # 停止
    if task.command == 0:
        video_task.stop()

    # 开始
    elif task.command == 1:
        video_task.start()

    # 删除
    else:
        video_task.delete()

    return {
        "resultCode": "200",
        "resultValue": None,
        "resultHint": None
    }


@router.post(
    "/analysis/api/analyseResult",
    description="视频分析结果返回测试接口",
)
async def video_task(
        analyse_result: AnalyseResultSchema
):
    res = dict(analyse_result)
    new = res['ImageData']
    filename = res['filename']
    if new is not None:
        with open(f'./{filename}', 'wb') as f:
            f.write(base64.b64decode(new))

    del res['ImageData']
