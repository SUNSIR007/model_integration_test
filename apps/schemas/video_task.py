from typing import Optional

from pydantic import BaseModel


class VideoTaskConfig(BaseModel):
    alarm_name: str
    model_name: str
    camera_id: int
    algorithm_id: int
    video_stream_url: str
    interval: int
    model_type: str
    return_url: Optional[str] = None
