from typing import List, Optional

from pydantic import BaseModel

PROCESSING_RUNNING = "RUNNING"
PROCESSING_STARTING = "STARTING"
PROCESSING_NO_SOURCE = "NO_SOURCE"
PROCESSING_MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
PROCESSING_ERROR = "ERROR"


class AlertInfo(BaseModel):
    id: int
    type: str
    severity: str
    message: str
    zone: str
    timestamp: str


class TelemetryMessage(BaseModel):
    timestamp: str
    zone: str
    personCount: int
    maxCapacity: int
    densityStatus: str
    fps: float
    evacuationRoute: str
    activeSource: str

    status: str = PROCESSING_STARTING
    error: Optional[str] = None
    alerts: List[AlertInfo] = []