from pydantic import BaseModel


class VoOmaPayload(BaseModel):
    id: float
    value: str


class Response(BaseModel):
    ok: bool
    data: float | str
