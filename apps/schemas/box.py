from datetime import datetime

from pydantic import BaseModel, Field


class UpdateSystemNameRequest(BaseModel):
    system_name: str


class UpdateTimeRequest(BaseModel):
    timeZone: str = Field(..., description="时区")
    date: datetime = Field(..., description="日期和时间")


class UpdateIpRequest(BaseModel):
    ip_address: str