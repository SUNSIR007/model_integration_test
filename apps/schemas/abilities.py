from datetime import datetime
from pydantic import BaseModel
from enum import Enum
from typing import Optional, List


# 定义命令枚举
class CommandEnum(int, Enum):
    STOP = 0
    START = 1
    DELETE = 2


# 视频流信息
class VideoInfoSchema(BaseModel):
    analyseId: str
    videoUrl: str


# 算法参数
class RuleAlgParamsSchema(BaseModel):
    key: Optional[str]
    value: Optional[str]


# 视频任务
class VideoTaskSchame(BaseModel):
    modelName: str
    startTime: datetime
    endTime: datetime
    interval: int
    command: CommandEnum
    videoInfo: List[VideoInfoSchema]


# 分析结果
class AnalyseResultSchema(BaseModel):
    modelName: Optional[str]
    analyseId: str
    analyseTime: Optional[datetime]
    analyseResults: List[dict]
    filename: Optional[str]
    ImageData: Optional[str]
