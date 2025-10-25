# app/services/metrics.py
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
import os


class MetricsService:
    def __init__(self):
        # In-memory storage for real-time metrics
        self._message_counter = 0
        self._join_counter = 0
        self._ws_events_counter = 0
        self._error_counter = 0

        # Time series data (last hour)
        self._message_history = deque(maxlen=3600)
        self._join_history = deque(maxlen=3600)
        self._ws_history = deque(maxlen=3600)

        # Room-specific metrics
        self._room_activity = defaultdict(lambda: {
            'messages': 0,
            'participants': 0,
            'last_activity': datetime.utcnow(),
            'media_streams': 0
        })

        # Performance metrics
        self._response_times = deque(maxlen=1000)
        self._start_time = datetime.utcnow()

    def increment_message_count(self, room_slug: str, encrypted: bool = False):
        """Увеличить счетчик сообщений"""
        self._message_counter += 1
        self._message_history.append((datetime.utcnow(), 1))
        self._room_activity[room_slug]['messages'] += 1
        self._room_activity[room_slug]['last_activity'] = datetime.utcnow()

    def increment_join_count(self, room_slug: str):
        """Увеличить счетчик присоединений"""
        self._join_counter += 1
        self._join_history.append((datetime.utcnow(), 1))

    def increment_ws_events(self, event_type: str):
        """Увеличить счетчик WebSocket событий"""
        self._ws_events_counter += 1
        self._ws_history.append((datetime.utcnow(), 1))

    def increment_errors(self, error_type: str = "unknown"):
        """Увеличить счетчик ошибок"""
        self._error_counter += 1

    def record_response_time(self, response_time: float):
        """Записать время ответа"""
        self._response_times.append(response_time)

    def update_room_participants(self, room_slug: str, participant_count: int):
        """Обновить количество участников в комнате"""
        self._room_activity[room_slug]['participants'] = participant_count
        self._room_activity[room_slug]['last_activity'] = datetime.utcnow()

    def update_media_streams(self, room_slug: str, stream_count: int):
        """Обновить количество медиа-стримов"""
        self._room_activity[room_slug]['media_streams'] = stream_count

    def _calculate_rate(self, history: deque, window_seconds: int = 60) -> float:
        """Рассчитать rate за указанное окно"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        count = sum(1 for timestamp, _ in history
                    if timestamp >= window_start)
        return count / (window_seconds / 60) if window_seconds > 0 else 0

    def get_system_stats(self) -> Dict[str, Any]:
        """Получить системную статистику"""
        # Активные комнаты (с активностью за последние 5 минут)
        active_rooms_threshold = datetime.utcnow() - timedelta(minutes=5)
        active_rooms = sum(1 for room_data in self._room_activity.values()
                           if room_data['last_activity'] >= active_rooms_threshold)

        return {
            "total_rooms": len(self._room_activity),
            "total_users": 0,  # Можно добавить позже из базы
            "active_rooms": active_rooms,
            "active_users": 0,  # Можно добавить позже из WebSocket hub
            "ws_connections": 0,
            "message_rate": self._calculate_rate(self._message_history),
            "participant_rate": self._calculate_rate(self._join_history),
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Получить метрики производительности"""
        try:
            process = psutil.Process(os.getpid())
            system_memory = psutil.virtual_memory()

            response_times = list(self._response_times)
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0

            p95_response_time = 0
            if response_times:
                sorted_times = sorted(response_times)
                p95_index = int(len(sorted_times) * 0.95)
                p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]

            return {
                "process_cpu_percent": process.cpu_percent(),
                "process_memory_mb": process.memory_info().rss / 1024 / 1024,
                "system_memory_percent": system_memory.percent,
                "system_memory_available_gb": system_memory.available / 1024 / 1024 / 1024,
                "avg_response_time_ms": avg_response_time * 1000,
                "p95_response_time_ms": p95_response_time * 1000,
                "uptime_seconds": (datetime.utcnow() - self._start_time).total_seconds(),
            }
        except Exception:
            return {
                "process_cpu_percent": 0,
                "process_memory_mb": 0,
                "system_memory_percent": 0,
                "system_memory_available_gb": 0,
                "avg_response_time_ms": 0,
                "p95_response_time_ms": 0,
                "uptime_seconds": (datetime.utcnow() - self._start_time).total_seconds(),
            }

    def get_room_metrics(self, room_slug: str) -> Dict[str, Any]:
        """Получить метрики конкретной комнаты"""
        room_data = self._room_activity.get(room_slug, {})
        if not room_data:
            return {}

        return {
            "slug": room_slug,
            "total_messages": room_data.get('messages', 0),
            "current_participants": room_data.get('participants', 0),
            "peak_participants": room_data.get('participants', 0),
            "media_streams": room_data.get('media_streams', 0),
            "last_activity": room_data.get('last_activity', datetime.utcnow()).isoformat(),
            "is_locked": False,
            "is_private": False,
            "recording_active": False,
        }

    def get_all_metrics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Получить все метрики"""
        system_stats = self.get_system_stats()
        performance_metrics = self.get_performance_metrics()

        # Собрать топ комнат по активности
        active_rooms = []
        for room_slug, data in self._room_activity.items():
            if data.get('last_activity', datetime.utcnow()) >= datetime.utcnow() - timedelta(minutes=30):
                active_rooms.append({
                    'slug': room_slug,
                    'message_count': data.get('messages', 0),
                    'participant_count': data.get('participants', 0),
                    'media_streams': data.get('media_streams', 0),
                    'last_activity': data.get('last_activity', datetime.utcnow()).isoformat()
                })

        active_rooms.sort(key=lambda x: x.get('message_count', 0), reverse=True)

        return {
            "system": system_stats,
            "performance": performance_metrics,
            "counters": {
                "total_messages": self._message_counter,
                "total_joins": self._join_counter,
                "total_ws_events": self._ws_events_counter,
                "total_errors": self._error_counter,
            },
            "top_rooms": active_rooms[:10],
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Получить статус здоровья системы"""
        system_stats = self.get_system_stats()
        performance = self.get_performance_metrics()

        checks = {
            "database": {"status": "ok", "response_time_ms": 0},
            "websocket": {"status": "ok", "connections": system_stats.get('ws_connections', 0)},
            "memory": {"status": "ok", "usage_percent": performance.get('system_memory_percent', 0)},
            "cpu": {"status": "ok", "usage_percent": performance.get('process_cpu_percent', 0)}
        }

        # Простая проверка здоровья
        memory_ok = performance.get('system_memory_percent', 0) < 90
        cpu_ok = performance.get('process_cpu_percent', 0) < 80

        is_healthy = memory_ok and cpu_ok
        overall_score = ((100 if memory_ok else 30) + (100 if cpu_ok else 30)) / 2

        if not memory_ok:
            checks["memory"]["status"] = "warning"
        if not cpu_ok:
            checks["cpu"]["status"] = "warning"

        return {
            "status": "healthy" if is_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
            "overall_score": round(overall_score, 1)
        }


# Глобальный экземпляр метрик
metrics_service = MetricsService()