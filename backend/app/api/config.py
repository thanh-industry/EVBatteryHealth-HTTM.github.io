from fastapi import APIRouter

from app.core.config import settings
from app.schemas.config import ThresholdsResponse

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/thresholds", response_model=ThresholdsResponse)
def get_thresholds() -> ThresholdsResponse:
    return ThresholdsResponse(good_min=settings.SOH_GOOD_MIN, monitor_min=settings.SOH_MONITOR_MIN)
