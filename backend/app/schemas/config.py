from pydantic import BaseModel


class ThresholdsResponse(BaseModel):
    good_min: float
    monitor_min: float
