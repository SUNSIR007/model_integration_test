import cv2
import gc 

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ultralytics import YOLO

from apps.database import get_db_session
from apps.models import Algorithm, Camera, Account
from apps.config import settings
from apps.routers.v1.auth import get_current_user

router = APIRouter(tags=["流媒体推理"])


def generate_frames(video_url, model):
    cap = cv2.VideoCapture(video_url)
    while cap.isOpened():
        success, frame = cap.read()

        if success:
            results = model(frame, device=settings.device)
            annotated_frame = results[0].plot()
            _, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()

            yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'

        else:
            break
        gc.collect()
    cap.release()


@router.get(
    '/video_feed',
    description="流媒体推理",
)
async def video_feed(
        camera_id: int,
        algorithm_id: int,
        session: Session = Depends(get_db_session),
        # current_user: Account = Depends(get_current_user)
):
    # if not current_user.is_active:
    #     raise HTTPException(
    #         status_code=403,
    #         detail="Access denied",
    #     )

    model_name = session.query(Algorithm).filter(Algorithm.id == algorithm_id).first().modelName
    video_url = session.query(Camera).filter(Camera.camera_id == camera_id).first().video_url
    model = YOLO(f'apps/detection/weights/{model_name}')
    return StreamingResponse(generate_frames(video_url, model), media_type='multipart/x-mixed-replace; boundary=frame')

