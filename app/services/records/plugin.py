from fastapi import APIRouter

from app.services.records import chart

router = APIRouter()
router.include_router(chart.router)
