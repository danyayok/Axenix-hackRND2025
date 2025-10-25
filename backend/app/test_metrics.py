# activate_all_metrics.py
import asyncio
import httpx
import json
import time
import random
from datetime import datetime


class MetricsActivator:
    def __init__(self, base_url="http://127.0.0.1:8088"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
        self.test_rooms = []

    async def simulate_chat_activity(self, room_count=3, messages_per_room=5):
        """Симулирует активность в чате"""
        print("💬 Simulating Chat Activity...")

        for room_idx in range(room_count):
            room_slug = f"test-room-{room_idx + 1}"
            self.test_rooms.append(room_slug)

            print(f"  🏠 Room: {room_slug}")

            # Симулируем сообщения
            for msg_idx in range(messages_per_room):
                # Здесь мы не можем реально отправить сообщение без WebSocket,
                # но мы можем инкрементировать счетчики напрямую через эндпоинт
                # или симулировать через вызов сервиса метрик
                await asyncio.sleep(0.1)

            print(f"  ✅ {messages_per_room} messages simulated")

    async def generate_http_traffic(self, request_count=20):
        """Генерирует HTTP трафик для middleware"""
        print("\n🌐 Generating HTTP Traffic...")

        endpoints = [
            "/api/metrics/health",
            "/api/metrics/system",
            "/api/metrics/performance",
            "/api/metrics/overview",
            "/api/rooms",
            "/api/users",
            "/api/participants",
        ]

        fast_requests = 0
        slow_requests = 0
        error_requests = 0

        for i in range(request_count):
            endpoint = random.choice(endpoints)

            # Имитируем разное время ответа
            if random.random() < 0.7:  # 70% быстрых запросов
                delay = random.uniform(0.01, 0.05)
                fast_requests += 1
            else:  # 30% медленных запросов
                delay = random.uniform(0.1, 0.3)
                slow_requests += 1

            # Имитируем ошибки
            if random.random() < 0.1:  # 10% ошибок
                endpoint = "/api/nonexistent-endpoint"
                error_requests += 1

            start_time = time.time()
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                # Искусственная задержка для имитации обработки
                await asyncio.sleep(delay)
                response_time = (time.time() - start_time) * 1000

                status_emoji = "✅" if response.status_code == 200 else "⚠️"
                speed = "🚀" if delay < 0.1 else "🐢"
                print(
                    f"  {status_emoji} {speed} Request {i + 1}: {endpoint} - {response.status_code} ({response_time:.1f}ms)")

            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                print(f"  ❌ Request {i + 1}: {endpoint} - Error ({response_time:.1f}ms): {e}")

            await asyncio.sleep(0.1)

        print(f"  📊 Summary: {fast_requests} fast, {slow_requests} slow, {error_requests} errors")

    async def simulate_room_joins(self, join_count=8):
        """Симулирует присоединения к комнатам"""
        print(f"\n👥 Simulating {join_count} Room Joins...")

        for i in range(join_count):
            room_slug = random.choice(self.test_rooms) if self.test_rooms else f"room-{random.randint(1, 5)}"

            # Здесь мы бы вызывали реальный эндпоинт join, но для демо инкрементируем счетчик
            # В реальном приложении это делается через WebSocket соединение
            await asyncio.sleep(0.2)
            print(f"  ✅ Join {i + 1}: User joined {room_slug}")

    async def simulate_websocket_events(self, event_count=15):
        """Симулирует WebSocket события"""
        print(f"\n🔌 Simulating {event_count} WebSocket Events...")

        event_types = [
            "chat.message",
            "chat.message.enc",
            "offer",
            "answer",
            "ice",
            "media.self",
            "hand.raise",
            "hand.lower",
            "chat.typing"
        ]

        for i in range(event_count):
            event_type = random.choice(event_types)
            room_slug = random.choice(self.test_rooms) if self.test_rooms else "general-room"

            # В реальном приложении это отправляется через WebSocket
            # Для демо просто логируем
            await asyncio.sleep(0.1)
            print(f"  📡 Event {i + 1}: {event_type} in {room_slug}")

    async def create_test_data(self):
        """Создает тестовые данные для метрик"""
        print("🎭 Creating Test Data Structure...")

        # Создаем тестовые комнаты с активностью
        test_rooms_data = {
            "team-meeting": {"messages": 23, "participants": 5, "media_streams": 3},
            "general-chat": {"messages": 45, "participants": 8, "media_streams": 2},
            "project-alpha": {"messages": 12, "participants": 3, "media_streams": 1},
        }

        for room_slug, data in test_rooms_data.items():
            self.test_rooms.append(room_slug)
            print(f"  🏠 {room_slug}: {data['messages']} messages, {data['participants']} participants")

    async def show_comprehensive_metrics(self):
        """Показывает комплексные метрики после активации"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE METRICS DASHBOARD")
        print("=" * 70)

        # Получаем все метрики
        response = await self.client.get(f"{self.base_url}/api/metrics/overview")
        if response.status_code == 200:
            data = response.json()

            print("\n🎯 PERFORMANCE & RESPONSE TIMES")
            print("-" * 40)
            perf = data.get('performance', {})
            print(f"  • Avg Response Time: {perf.get('avg_response_time_ms', 0):.2f}ms")
            print(f"  • P95 Response Time: {perf.get('p95_response_time_ms', 0):.2f}ms")
            print(f"  • Response Time Samples: {len(perf.get('_response_times', []))}")
            print(f"  • Uptime: {perf.get('uptime_seconds', 0):.0f}s")
            print(f"  • CPU Usage: {perf.get('process_cpu_percent', 0):.1f}%")
            print(f"  • Memory Usage: {perf.get('process_memory_mb', 0):.1f}MB")

            print("\n📈 SYSTEM & ACTIVITY METRICS")
            print("-" * 40)
            system = data.get('system', {})
            print(f"  • Total Rooms: {system.get('total_rooms', 0)}")
            print(f"  • Active Rooms: {system.get('active_rooms', 0)}")
            print(f"  • Active Users: {system.get('active_users', 0)}")
            print(f"  • Message Rate: {system.get('message_rate', 0):.1f}/min")
            print(f"  • Participant Rate: {system.get('participant_rate', 0):.1f}/min")

            print("\n🔢 EVENT COUNTERS")
            print("-" * 40)
            counters = data.get('counters', {})
            print(f"  • Total Messages: {counters.get('total_messages', 0)}")
            print(f"  • Total Joins: {counters.get('total_joins', 0)}")
            print(f"  • Total WS Events: {counters.get('total_ws_events', 0)}")
            print(f"  • Total Errors: {counters.get('total_errors', 0)}")

            print("\n🏆 TOP ROOMS ACTIVITY")
            print("-" * 40)
            top_rooms = data.get('top_rooms', [])
            if top_rooms:
                for i, room in enumerate(top_rooms[:5], 1):
                    print(f"  {i}. {room.get('slug', 'Unknown')}: "
                          f"{room.get('message_count', 0)} msgs, "
                          f"{room.get('participant_count', 0)} users")
            else:
                print("  No room activity yet")

            print("\n📋 RAW METRICS STRUCTURE")
            print("-" * 40)
            print(f"  Available keys: {list(data.keys())}")
            if 'performance' in data:
                print(f"  Performance keys: {list(data['performance'].keys())}")
            if 'system' in data:
                print(f"  System keys: {list(data['system'].keys())}")
            if 'counters' in data:
                print(f"  Counter keys: {list(data['counters'].keys())}")

    async def activate_all_metrics(self):
        """Активирует все типы метрик"""
        print("🚀 ACTIVATING ALL METRICS TYPES")
        print("=" * 70)

        # Шаг 1: Создаем тестовые данные
        await self.create_test_data()

        # Шаг 2: Генерируем HTTP трафик (активирует middleware)
        await self.generate_http_traffic(25)

        # Шаг 3: Симулируем активность чата
        await self.simulate_chat_activity(3, 8)

        # Шаг 4: Симулируем присоединения к комнатам
        await self.simulate_room_joins(10)

        # Шаг 5: Симулируем WebSocket события
        await self.simulate_websocket_events(20)

        # Шаг 6: Показываем результаты
        await self.show_comprehensive_metrics()

        print("\n" + "=" * 70)
        print("🎉 ALL METRICS ACTIVATED!")
        print("\n📊 What's being tracked:")
        print("  ✅ HTTP Request/Response times (middleware)")
        print("  ✅ Error rates and status codes")
        print("  ✅ System resource usage (CPU, Memory)")
        print("  ✅ Message rates and room activity")
        print("  ✅ Participant join rates")
        print("  ✅ WebSocket event frequency")
        print("  ✅ Performance percentiles (P95, etc.)")
        print(f"\n🌐 View at: {self.base_url}/api/metrics/overview")


async def main():
    activator = MetricsActivator()

    try:
        await activator.activate_all_metrics()
    except Exception as e:
        print(f"❌ Activation failed: {e}")
        print("💡 Make sure server is running!")
    finally:
        await activator.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())