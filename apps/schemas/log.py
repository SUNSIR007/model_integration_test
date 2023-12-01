from typing import List, Any
from pydantic import BaseModel


class OperateLogResp(BaseModel):
    traceId: str
    userId: int
    module: str
    name: str
    type: int
    content: str
    exts: Any
    requestMethod: str
    requestUrl: str
    userIp: str
    userAgent: str
    pythonMethod: str
    pythonMethodArgs: str
    startTime: str
    duration: int
    resultCode: int
    resultMsg: str
    resultData: str
    id: int
    userNickname: str


class PageResultOperateLogResp(BaseModel):
    list: List[OperateLogResp]
    total: int


class OperateLogPageResponse(BaseModel):
    code: int
    data: PageResultOperateLogResp
    msg: str
