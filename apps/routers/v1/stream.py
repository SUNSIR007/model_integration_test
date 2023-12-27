import cv2
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ultralytics import YOLO

from apps.database import get_db_session
from apps.models import Algorithm, Camera


router = APIRouter(tags=["流媒体推理"])


def generate_frames(video_url, model):
    cap = cv2.VideoCapture(video_url)
    while cap.isOpened():
        success, frame = cap.read()

        if success:
            results = model(frame)
            annotated_frame = results[0].plot()
            _, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()

            yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'

        else:
            break
    cap.release()


@router.get(
    '/video_feed',
    description="流媒体推理",
)
def video_feed(
        camera_id: int,
        algorithm_id: int,
        session: Session = Depends(get_db_session)
):
    model_name = session.query(Algorithm).filter(Algorithm.id==algorithm_id).first().modelName
    video_url = session.query(Camera).filter(Camera.camera_id==camera_id).first().video_url
    model = YOLO(f'apps/detection/weights/{model_name}')
    return StreamingResponse(generate_frames(video_url, model), media_type='multipart/x-mixed-replace; boundary=frame')
