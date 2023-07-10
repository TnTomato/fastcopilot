from typing import Callable, Awaitable

from pydantic import BaseModel


class FuncSpec(BaseModel):
    json_schema: dict
    handler: Callable | Awaitable

    class Config:
        arbitrary_types_allowed = True
