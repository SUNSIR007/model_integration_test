from pydantic import BaseModel


class VideoParams(BaseModel):
    video_path: str
