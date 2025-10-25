# app/middleware/metrics_middleware.py
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.services.metrics import metrics_service  # Используем глобальный экземпляр


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)

            # Записываем время ответа
            response_time = time.time() - start_time
            metrics_service.record_response_time(response_time)

            # Счетчик ошибок для статусов 5xx
            if 500 <= response.status_code < 600:
                metrics_service.increment_errors(f"http_{response.status_code}")

            return response

        except Exception as e:
            metrics_service.increment_errors(f"exception_{type(e).__name__}")
            raise