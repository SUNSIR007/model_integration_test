from fastapi import APIRouter, status, Depends, HTTPException

from apps.models import Account
from apps.routers.v1.auth import get_current_user
from apps.schemas import GeneralResponse
from apps.utils.easycvr import convert_rtsp_to_http
from apps.schemas.easycvr import RtspInfo

router = APIRouter(tags=["视频流转码"])


@router.post(
    '/video/transport',
    status_code=status.HTTP_200_OK,
    description="RTSP视频转码HTTP",
)
async def transport_video(
        rtsp_info: RtspInfo,
        current_user: Account = Depends(get_current_user),
) -> GeneralResponse:
    if not current_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    http_url = convert_rtsp_to_http(**rtsp_info.dict())

    return GeneralResponse(
        code=200,
        data={
            "rtspUrl": rtsp_info.rtsp_url,
            "httpUrl": http_url
        }
    )
