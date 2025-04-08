from typing import List

from pydantic import BaseModel


class EsaoteDataValue(BaseModel):
    v: float


class EsaoteData(BaseModel):
    tmstp: str
    e: List[EsaoteDataValue]


class VoOmaResource(BaseModel):
    id: str
    value: float


class Response(BaseModel):
    ok: bool
    data: float
