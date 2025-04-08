import random

import uvicorn
from fastapi import FastAPI
from model import Response, VoOmaResource

app = FastAPI()


for object_id in [3319, 33320, 33321, 33322]:
    @app.get(f"/1/{object_id}/1/1", response_model=VoOmaResource)
    async def read(getRealtime: bool = False) -> VoOmaResource:
        return VoOmaResource(id="1", value=random.uniform(0, 30))

    @app.put(f"/1/{object_id}/1/1", response_model=Response)
    async def write(vo_oma_res: VoOmaResource) -> Response:
        return Response(ok=True, value=vo_oma_res.value)

if __name__ == "__main__":
    uvicorn.run("rest-api:app", host="0.0.0.0", port=5555, reload=True)
