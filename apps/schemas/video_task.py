from pydantic import BaseModel


class VideoTaskConfig(BaseModel):
    model_name: str
    camera_id: int
    algorithm_id: int
    video_stream_url: str
    interval: int
    model_type: str
