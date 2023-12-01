from typing import List
from pydantic import BaseModel


class AlgorithmInfoResp(BaseModel):
    name: str
    modelName: str
    version: str
    repoSource: str
    id: int
    createTime: str


class PageResultAlgorithmInfoResp(BaseModel):
    list: List[AlgorithmInfoResp]
    total: int

