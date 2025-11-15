import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import json
import time
import uuid


class TestVideoConferenceAPIUnit:

    @pytest.fixture
    def test_instance(self):
        """Фикстура для создания экземпляра тестового класса"""
        from backend.tests import TestVideoConferenceAPI
        instance = TestVideoConferenceAPI()
        instance.setup_method()
        return instance

    @pytest.fixture
    def mock_response(self):
        """Фикстура для создания мока ответа requests"""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {}
        response.text = ""
        return response

    def test_init(self, test_instance):
        """Тест инициализации класса"""
        assert test_instance.created_rooms == []
        assert test_instance.created_users == []

    def test_setup_method(self, test_instance):
        """Тест метода setup_method"""
        test_instance.created_rooms = ["test_room"]
        test_instance.created_users = ["test_user"]
        test_instance.setup_method()
        assert test_instance.created_rooms == []
        assert test_instance.created_users == []

    @patch('requests.get')
    def test_test_01_swagger_docs_available_success(self, mock_get, test_instance, mock_response):
        """Тест успешной проверки доступности Swagger UI"""
        mock_response.status_code = 200
        mock_response.text = "Swagger UI content"
        mock_get.return_value = mock_response

        result = test_instance.test_01_swagger_docs_available()
        assert result is True
        mock_get.assert_called_once_with("http://127.0.0.1:8088/docs")

    @patch('requests.get')
    def test_test_01_swagger_docs_available_failure(self, mock_get, test_instance, mock_response):
        """Тест неуспешной проверки доступности Swagger UI"""
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(AssertionError):
            test_instance.test_01_swagger_docs_available()

    @patch('requests.get')
    def test_test_02_openapi_schema_available_success(self, mock_get, test_instance, mock_response):
        """Тест успешной проверки доступности OpenAPI схемы"""
        mock_response.status_code = 200
        mock_response.json.return_value = {"openapi": "3.0.0", "paths": {}, "components": {}}
        mock_get.return_value = mock_response

        result = test_instance.test_02_openapi_schema_available()
        assert result is True
        mock_get.assert_called_once_with("http://127.0.0.1:8088/openapi.json")

    @patch('requests.get')
    def test_test_02_openapi_schema_available_missing_fields(self, mock_get, test_instance, mock_response):
        """Тест проверки OpenAPI схемы с отсутствующими полями"""
        mock_response.status_code = 200
        mock_response.json.return_value = {"openapi": "3.0.0"}
        mock_get.return_value = mock_response

        with pytest.raises(AssertionError):
            test_instance.test_02_openapi_schema_available()

    @patch('requests.post')
    def test_test_03_create_user_success(self, mock_post, test_instance, mock_response):
        """Тест успешного создания пользователя"""
        user_id = str(uuid.uuid4())
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": user_id, "nickname": "testuser_12345"}
        mock_post.return_value = mock_response

        result = test_instance.test_03_create_user()
        assert result == user_id
        assert user_id in test_instance.created_users
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_test_03_create_user_failure(self, mock_post, test_instance, mock_response):
        """Тест неуспешного создания пользователя"""
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        with pytest.raises(AssertionError):
            test_instance.test_03_create_user()

    @patch('requests.post')
    def test_test_04_create_room_correct_schema_success(self, mock_post, test_instance, mock_response):
        """Тест успешного создания комнаты с правильной схемой"""
        mock_response.status_code = 201
        mock_response.json.return_value = {"slug": "test-room-123", "id": "room-id"}
        mock_post.return_value = mock_response

        result = test_instance.test_04_create_room_correct_schema()
        assert result == "test-room-123"
        assert "test-room-123" in test_instance.created_rooms

    @patch('requests.post')
    def test_test_04_create_room_correct_schema_validation_error(self, mock_post, test_instance, mock_response):
        """Тест создания комнаты с ошибкой валидации"""
        mock_response.status_code = 422
        mock_response.json.return_value = {"detail": [{"loc": ["body", "title"], "msg": "field required"}]}
        mock_post.return_value = mock_response

        with patch.object(test_instance, '_try_alternative_room_creation', return_value="fail"):
            result = test_instance.test_04_create_room_correct_schema()
            assert result == "fail"

    @patch('requests.post')
    def test_test_04_create_room_correct_schema_unexpected_status(self, mock_post, test_instance, mock_response):
        """Тест создания комнаты с неожиданным статус кодом"""
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = test_instance.test_04_create_room_correct_schema()
        assert result == "fail"

    def test_try_alternative_room_creation_first_variant_success(self, test_instance):
        """Тест альтернативного создания комнаты - первый вариант успешный"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"slug": "simple-room-123"}
            mock_post.return_value = mock_response

            result = test_instance._try_alternative_room_creation()
            assert result == "simple-room-123"

    def test_try_alternative_room_creation_second_variant_success(self, test_instance):
        """Тест альтернативного создания комнаты - второй вариант успешный"""
        with patch('requests.post') as mock_post:
            # Первый вызов - ошибка
            first_response = Mock()
            first_response.status_code = 422
            # Второй вызов - успешное создание пользователя
            second_response = Mock()
            second_response.status_code = 200
            second_response.json.return_value = {"id": "user-123"}
            # Третий вызов - успешное создание комнаты
            third_response = Mock()
            third_response.status_code = 201
            third_response.json.return_value = {"slug": "room-with-user-123"}
            
            mock_post.side_effect = [first_response, second_response, third_response]

            with patch.object(test_instance, 'test_03_create_user', return_value="user-123"):
                result = test_instance._try_alternative_room_creation()
                assert result == "room-with-user-123"

    @patch('requests.get')
    def test_test_05_list_rooms_success(self, mock_get, test_instance, mock_response):
        """Тест успешного получения списка комнат"""
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "room1"}, {"id": "room2"}]
        mock_get.return_value = mock_response

        result = test_instance.test_05_list_rooms()
        assert result is True
        mock_get.assert_called_once_with(
            "http://127.0.0.1:8088/api/rooms",
            headers={"accept": "application/json"}
        )

    @patch('requests.get')
    def test_test_05_list_rooms_invalid_response(self, mock_get, test_instance, mock_response):
        """Тест получения списка комнат с невалидным ответом"""
        mock_response.status_code = 200
        mock_response.json.return_value = "not a list"
        mock_get.return_value = mock_response

        with pytest.raises(AssertionError):
            test_instance.test_05_list_rooms()

    @patch('requests.get')
    def test_test_06_get_room_by_slug_success(self, mock_get, test_instance, mock_response):
        """Тест успешного получения информации о комнате по slug"""
        mock_response.status_code = 200
        mock_response.json.return_value = {"slug": "test-room", "title": "Test Room"}
        mock_get.return_value = mock_response

        result = test_instance.test_06_get_room_by_slug()
        assert result is True

    @patch('requests.get')
    def test_test_06_get_room_by_slug_not_found(self, mock_get, test_instance, mock_response):
        """Тест получения информации о комнате по slug - комната не найдена"""
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = test_instance.test_06_get_room_by_slug()
        assert result is True

    @patch('requests.get')
    def test_test_07_room_exists_success(self, mock_get, test_instance, mock_response):
        """Тест успешной проверки существования комнаты"""
        mock_response.status_code = 200
        mock_response.json.return_value = {"exists": True}
        mock_get.return_value = mock_response

        result = test_instance.test_07_room_exists()
        assert result is True

    @patch('requests.get')
    def test_test_07_room_exists_invalid_response(self, mock_get, test_instance, mock_response):
        """Тест проверки существования комнаты с невалидным ответом"""
        mock_response.status_code = 200
        mock_response.json.return_value = {"exists": "not boolean"}
        mock_get.return_value = mock_response

        result = test_instance.test_07_room_exists()
        assert result is True

    @patch('requests.post')
    def test_test_08_guest_token_success(self, mock_post, test_instance, mock_response):
        """Тест успешного получения гостевого токена"""
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test-token", "token_type": "bearer"}
        mock_post.return_value = mock_response

        result = test_instance.test_08_guest_token()
        assert result is True

    @patch('requests.get')
    def test_test_09_rtc_config_success(self, mock_get, test_instance, mock_response):
        """Тест успешного получения RTC конфигурации"""
        mock_response.status_code = 200
        mock_response.json.return_value = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        mock_get.return_value = mock_response

        result = test_instance.test_09_rtc_config()
        assert result is True

    @patch('requests.post')
    def test_test_10_join_room_validation_not_found(self, mock_post, test_instance, mock_response):
        """Тест валидации присоединения к комнате - комната не найдена"""
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        result = test_instance.test_10_join_room_validation()
        assert result is True

    @patch('requests.post')
    def test_test_10_join_room_validation_error(self, mock_post, test_instance, mock_response):
        """Тест валидации присоединения к комнате - ошибка валидации"""
        mock_response.status_code = 422
        mock_response.json.return_value = {"detail": "validation error"}
        mock_post.return_value = mock_response

        result = test_instance.test_10_join_room_validation()
        assert result is True

    @pytest.mark.parametrize("test_case", [
        {"name": "Пустой заголовок", "data": {"title": "", "created_by": 1}, "expected_code": 422},
        {"name": "Отсутствует created_by", "data": {"title": "Test Room"}, "expected_code": 422},
        {"name": "Неправильный тип created_by", "data": {"title": "Test Room", "created_by": "not-integer"}, "expected_code": 422},
        {"name": "Неправильный тип is_private", "data": {"title": "Test Room", "created_by": 1, "is_private": "not-boolean"}, "expected_code": 422}
    ])
    @patch('requests.post')
    def test_test_11_validation_errors_detailed(self, mock_post, test_instance, mock_response, test_case):
        """Тест детальной проверки валидации"""
        mock_response.status_code = test_case["expected_code"]
        mock_response.json.return_value = {"detail": "validation error"}
        mock_post.return_value = mock_response

        result = test_instance.test_11_validation_errors_detailed()
        assert result is True

    def test_test_12_room_operations_workflow_skip(self, test_instance):
        """Тест workflow операций с комнатами - пропущен"""
        with patch.object(test_instance, 'test_03_create_user', return_value="user-123"), \
             patch.object(test_instance, 'test_04_create_room_correct_schema', return_value="fail"):
            
            result = test_instance.test_12_room_operations_workflow()
            assert result == "skip"

    @patch('requests.get')
    def test_test_13_swagger_schema_analysis_success(self, mock_get, test_instance, mock_response):
        """Тест успешного анализа Swagger схемы"""
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "paths": {
                "/api/rooms": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "title": {"type": "string"},
                                            "created_by": {"type": "integer"}
                                        },
                                        "required": ["title", "created_by"]
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {}
            }
        }
        mock_get.return_value = mock_response

        result = test_instance.test_13_swagger_schema_analysis()
        assert result is True

    @pytest.mark.parametrize("endpoint_data", [
        ("GET", "/api/rooms"),
        ("POST", "/api/users"),
        ("POST", "/api/auth/token/guest"),
        ("GET", "/api/rtc/config"),
        ("GET", "/api/rooms/test/exists"),
    ])
    @patch('requests.get')
    @patch('requests.post')
    def test_test_14_api_health_check_success(self, mock_post, mock_get, test_instance, mock_response, endpoint_data):
        """Тест успешной проверки здоровья API"""
        method, endpoint = endpoint_data
        mock_response.status_code = 200
        if method == "GET":
            mock_get.return_value = mock_response
        else:
            mock_post.return_value = mock_response

        result = test_instance.test_14_api_health_check()
        assert result is True