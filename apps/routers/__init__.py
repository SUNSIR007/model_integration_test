from fastapi import FastAPI

from apps.routers.v1 import router as v1_router


def setup_routers(app: FastAPI):
    app.include_router(v1_router)
