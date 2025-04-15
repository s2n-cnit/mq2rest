from pydantic import BaseModel


class EsaotePayload(BaseModel):
    Value: str


class VoOmaPayload(BaseModel):
    id: float
    value: str


class Response(BaseModel):
    ok: bool
    data: float | str
