from pydantic import BaseModel


class RtspInfo(BaseModel):
    device_name: str
    device_type: str = 'ipc'
    transport: str = 'TCP'
    channel_name: str
    protocol: str = 'RTSP'
    rtsp_url: str
    target_protocol: str = 'flv'
