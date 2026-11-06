from fastapi import APIRouter

from app.services.records import chart, consultations, prescriptions

router = APIRouter()
router.include_router(chart.router)
router.include_router(consultations.router)
router.include_router(prescriptions.router)
