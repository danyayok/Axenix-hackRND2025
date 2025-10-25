# schemas/metrics.py
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class MetricDataPoint(BaseModel):
    timestamp: datetime
    value: float
    labels: Optional[Dict[str, str]] = None

class MetricSeries(BaseModel):
    name: str
    type: str  # counter, gauge, histogram
    data_points: List[MetricDataPoint]
    description: Optional[str] = None

class MetricsResponse(BaseModel):
    metrics: List[MetricSeries]
    period_start: datetime
    period_end: datetime

class SystemStats(BaseModel):
    total_rooms: int
    total_users: int
    active_rooms: int
    active_users: int
    ws_connections: int
    message_rate: float
    participant_rate: float

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    checks: Dict[str, Any]
    overall_score: float