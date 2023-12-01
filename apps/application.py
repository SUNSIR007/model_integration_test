from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.routers import setup_routers
from .database import Base, engine

tags_metadata = [
    {
        "name": "model-integration",
        "description": "边缘计算盒子",
    },
]


def create_application():

    app = FastAPI(
        title="model-integration",
        version="0.1.0",
        openapi_tags=tags_metadata,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
    setup_routers(app)
    Base.metadata.create_all(bind=engine)

    return app
