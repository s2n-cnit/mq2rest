import random

import uvicorn
from fastapi import APIRouter, FastAPI
from model import Response, VoOmaPayload

app = FastAPI()
router = APIRouter(prefix="/api/clients")

devId = "D001"

for object_id in [3319, 33320, 33321, 33322]:
    @router.get(f"/{devId}/{object_id}/0/5700")
    async def read(getRealtime: bool = False) -> VoOmaPayload:
        return VoOmaPayload(id=5700, value=str(random.uniform(0, 30)))

    @router.put(f"/{devId}/{object_id}/0/5700")
    async def write(vo_oma_payload: VoOmaPayload) -> Response:
        return Response(ok=True, data=vo_oma_payload.value)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("rest-api:app", host="0.0.0.0", port=5555, reload=True)
