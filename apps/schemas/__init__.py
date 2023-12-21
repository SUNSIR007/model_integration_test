from typing import Any, List, Optional, Union, TypeVar, Dict

from pydantic import validator
from pydantic.generics import Generic, GenericModel
from pydantic.main import BaseModel

from .errors import errors

DataT = TypeVar("DataT")


class Response(GenericModel, Generic[DataT]):
    data: Optional[DataT]
    msg: Optional[str]
    code: int = 0

    @validator("msg", always=True)
    def check_consistency(cls, v, values):
        if v is not None and values.get("data") is not None:
            raise ValueError("must not provide both data and msg")
        if v is None and values.get("data") is None:
            raise ValueError("must provide data or msg")
        return v

    @validator("code", always=True)
    def check_code(cls, v, values: Dict):
        if v == 0 and values.get("data") is None:
            raise ValueError("code must be 0 if data is provided")
        if v > 0 and (
            values.get("msg") is None or values.get("msg").strip() == ""
        ):
            raise ValueError("code must not be 0 if msg is provided")
        return v


# TODO: Need to be deleted

class GeneralResponse(BaseModel):
    code: int
    data: Optional[Union[Any, List[Any]]]
    msg: Optional[str]


def get_error_response(error_code: int):
    return GeneralResponse(code=error_code, msg=errors.get(error_code))
