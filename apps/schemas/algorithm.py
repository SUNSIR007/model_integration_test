from typing import List
from pydantic import BaseModel


class AlgorithmInfoResp(BaseModel):
    name: str
    modelName: str
    version: str = None
    repoSource: str
    id: int
    createTime: str


class PageResultAlgorithmInfoResp(BaseModel):
    list: List[AlgorithmInfoResp]
    total: int


class AlgorithmCreate(BaseModel):
    name: str
    modelName: str
    modelType: str
    repoSource: str
