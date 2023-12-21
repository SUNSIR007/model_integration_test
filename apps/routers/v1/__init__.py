from fastapi import APIRouter

from apps.routers.v1.account import router as account_router
from apps.routers.v1.auth import router as auth_router
from apps.routers.v1.box import router as box_router
from apps.routers.v1.algorithm import router as algo_router
from apps.routers.v1.log import router as log_router
from apps.routers.v1.camera import router as camera_router
from apps.routers.v1.alarm import router as alarm_router
from apps.routers.v1.easycvr import router as easycvr_router


router = APIRouter()

router.include_router(account_router)
router.include_router(auth_router)
router.include_router(box_router)
router.include_router(algo_router)
router.include_router(log_router)
router.include_router(camera_router)
router.include_router(alarm_router)
router.include_router(easycvr_router)
