from fastapi import APIRouter

from irony.routers.agent.auth_router import router as auth_router
from irony.routers.agent.order_router import router as order_router
from irony.routers.agent.service_router import router as service_router

router = APIRouter(prefix="/agent")

router.include_router(auth_router)
router.include_router(order_router)
router.include_router(service_router)
