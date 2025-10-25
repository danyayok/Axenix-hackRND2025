# app/api/metrics.py
from fastapi import APIRouter, HTTPException, Query
from app.services.metrics import metrics_service
from app.schemas.metrics import SystemStats, HealthCheck

router = APIRouter()

@router.get("/system", response_model=SystemStats)
async def get_system_metrics():
    """Получить системные метрики"""
    return metrics_service.get_system_stats()

@router.get("/performance")
async def get_performance_metrics():
    """Получить метрики производительности"""
    return metrics_service.get_performance_metrics()

@router.get("/rooms/{room_slug}")
async def get_room_metrics(room_slug: str):
    """Получить метрики комнаты"""
    metrics = metrics_service.get_room_metrics(room_slug)
    if not metrics:
        raise HTTPException(status_code=404, detail="Room not found")
    return metrics

@router.get("/overview")
async def get_all_metrics(
    time_window: int = Query(60, description="Time window in minutes", ge=1, le=1440)
):
    """Получить полный обзор метрик"""
    return metrics_service.get_all_metrics(time_window)

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check с метриками"""
    return metrics_service.get_health_status()