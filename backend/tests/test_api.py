"""
🧪 Тесты для REST API

Тестирование всех API endpoints.
Принцип CyberKitty: простота превыше всего.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import AsyncMock, patch

from backend.src.api.main import app
from backend.src.api.routers.clients import get_client_service
from backend.src.api.routers.subscriptions import get_subscription_service
from backend.src.api.routers.notifications import get_notification_service
from backend.src.api.routers.analytics import (
    get_client_service as get_analytics_client_service,
    get_subscription_service as get_analytics_subscription_service,
    get_notification_service as get_analytics_notification_service
)
from backend.src.models.client import Client, ClientStatus
from backend.src.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from backend.src.models.notification import Notification, NotificationStatus, NotificationType, NotificationPriority


@pytest.fixture(scope="session")
def mock_services():
    """Глобальные моки сервисов для всех тестов."""
    from unittest.mock import AsyncMock
    
    return {
        'client_service': AsyncMock(),
        'subscription_service': AsyncMock(),
        'notification_service': AsyncMock()
    }


@pytest.fixture
def client(mock_services):
    """Тестовый клиент FastAPI."""
    
    # Переопределяем зависимости
    app.dependency_overrides = {
        get_client_service: lambda: mock_services['client_service'],
        get_subscription_service: lambda: mock_services['subscription_service'],
        get_notification_service: lambda: mock_services['notification_service'],
        # Analytics dependencies
        get_analytics_client_service: lambda: mock_services['client_service'],
        get_analytics_subscription_service: lambda: mock_services['subscription_service'],
        get_analytics_notification_service: lambda: mock_services['notification_service'],
    }
    
    yield TestClient(app)
    
    # Очищаем переопределения после тестов
    app.dependency_overrides.clear()


@pytest.fixture
def sample_client():
    """Образец клиента для тестов."""
    return Client(
        id="test-client-1",
        name="Тест Клиент",
        phone="+79991234567",
        telegram_id=123456789,
        yoga_experience=True,
        intensity_preference="средняя",
        time_preference="утро",
        age=25,
        injuries="Нет",
        goals="Здоровье",
        how_found_us="Интернет",
        status=ClientStatus.ACTIVE,
        created_at=datetime.now()
    )


@pytest.fixture
def sample_subscription():
    """Образец абонемента для тестов."""
    from datetime import date, timedelta
    return Subscription(
        id="test-subscription-1",
        client_id="test-client-1",
        type=SubscriptionType.PACKAGE_8,
        total_classes=8,
        used_classes=2,
        remaining_classes=6,
        price=9600,
        status=SubscriptionStatus.ACTIVE,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_notification():
    """Образец уведомления для тестов."""
    # Создаем объект уведомления с правильными полями
    now = datetime.now()
    return Notification(
        id="test-notification-1",
        client_id="test-client-1",
        type=NotificationType.GENERAL_INFO,
        title="Тестовое уведомление",
        message="Это тестовое сообщение",
        priority=NotificationPriority.NORMAL,
        status=NotificationStatus.PENDING,
        scheduled_at=None,
        sent_at=None,
        delivered_at=None,
        failed_at=None,
        retry_count=0,
        max_retries=3,
        metadata={},
        created_at=now,
        updated_at=now
    )


class TestHealthCheck:
    """Тесты health check endpoint."""
    
    def test_health_check(self, client):
        """Тест проверки состояния API."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "practiti-admin-api"
        assert data["version"] == "1.0.0"


class TestClientsAPI:
    """Тесты API клиентов."""
    
    def test_get_clients_list(self, client, sample_client, mock_services):
        """Тест получения списка клиентов."""
        # Настраиваем мок сервиса
        mock_services['client_service'].get_all_clients.return_value = [sample_client]
        
        response = client.get("/api/v1/clients/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["limit"] == 20
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Тест Клиент"
    
    def test_get_client_by_id(self, client, sample_client, mock_services):
        """Тест получения клиента по ID."""
        # Настраиваем мок сервиса
        mock_services['client_service'].get_client.return_value = sample_client
        
        response = client.get("/api/v1/clients/test-client-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-client-1"
        assert data["name"] == "Тест Клиент"
        assert data["phone"] == "+79991234567"
    
    def test_create_client(self, client, sample_client, mock_services):
        """Тест создания клиента."""
        # Настраиваем мок сервиса
        mock_services['client_service'].create_client.return_value = sample_client
        
        client_data = {
            "name": "Тест Клиент",
            "phone": "+79991234567",
            "telegram_id": 123456789,
            "yoga_experience": True,
            "intensity_preference": "средняя",
            "time_preference": "утро",
            "age": 25,
            "injuries": "Нет",
            "goals": "Здоровье",
            "how_found_us": "Интернет"
        }
        
        response = client.post("/api/v1/clients/", json=client_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Тест Клиент"
        assert data["phone"] == "+79991234567"
    
    def test_client_not_found(self, client, mock_services):
        """Тест получения несуществующего клиента."""
        from backend.src.utils.exceptions import BusinessLogicError
        
        # Настраиваем мок сервиса
        mock_services['client_service'].get_client.side_effect = BusinessLogicError("Клиент не найден")
        
        response = client.get("/api/v1/clients/nonexistent")
        
        assert response.status_code == 404


class TestSubscriptionsAPI:
    """Тесты API абонементов."""
    
    def test_get_subscriptions_list(self, client, sample_subscription, mock_services):
        """Тест получения списка абонементов."""
        # Настраиваем мок сервиса
        mock_services['subscription_service'].get_all_subscriptions.return_value = [sample_subscription]
        
        response = client.get("/api/v1/subscriptions/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["client_id"] == "test-client-1"
    
    def test_create_subscription(self, client, sample_subscription, mock_services):
        """Тест создания абонемента."""
        # Настраиваем мок сервиса
        mock_services['subscription_service'].create_subscription.return_value = sample_subscription
        
        subscription_data = {
            "client_id": "test-client-1",
            "subscription_type": "package_8",
            "classes_total": 8,
            "price_paid": 9600.0,
            "payment_method": "card",
            "notes": "Тестовый абонемент"
        }
        
        response = client.post("/api/v1/subscriptions/", json=subscription_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["client_id"] == "test-client-1"
        assert data["total_classes"] == 8
    
    def test_use_class(self, client, sample_subscription, mock_services):
        """Тест использования занятия."""
        # Настраиваем мок сервиса
        mock_services['subscription_service'].use_class.return_value = sample_subscription
        
        use_class_data = {
            "subscription_id": "test-subscription-1",
            "class_date": "2024-01-15T10:00:00",
            "class_type": "Hatha Yoga",
            "instructor": "Анна",
            "notes": "Отличное занятие"
        }
        
        response = client.post("/api/v1/subscriptions/test-subscription-1/use-class", json=use_class_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-subscription-1"


class TestNotificationsAPI:
    """Тесты API уведомлений."""
    
    def test_get_notifications_list(self, client, sample_notification, mock_services):
        """Тест получения списка уведомлений."""
        # Настраиваем мок сервиса
        mock_services['notification_service'].get_all_notifications.return_value = [sample_notification]
        
        response = client.get("/api/v1/notifications/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["client_id"] == "test-client-1"
    
    def test_create_notification(self, client, sample_notification, mock_services):
        """Тест создания уведомления."""
        # Настраиваем мок сервиса
        mock_services['notification_service'].create_notification.return_value = sample_notification
        
        notification_data = {
            "client_id": "test-client-1",
            "notification_type": "general_info",
            "title": "Тестовое уведомление",
            "message": "Это тестовое сообщение",
            "metadata": {}
        }
        
        response = client.post("/api/v1/notifications/", json=notification_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["client_id"] == "test-client-1"
        assert data["title"] == "Тестовое уведомление"
    
    def test_send_notification(self, client, sample_notification, mock_services):
        """Тест отправки уведомления."""
        # Настраиваем мок сервиса
        mock_services['notification_service'].send_notification.return_value = True
        mock_services['notification_service'].get_notification.return_value = sample_notification
        
        response = client.post("/api/v1/notifications/test-notification-1/send")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-notification-1"


class TestAnalyticsAPI:
    """Тесты API аналитики."""
    
    def test_overview_analytics(self, client, sample_client, sample_subscription, sample_notification, mock_services):
        """Тест общей аналитики."""
        # Настраиваем моки
        mock_services['client_service'].get_all_clients.return_value = [sample_client]
        mock_services['subscription_service'].get_all_subscriptions.return_value = [sample_subscription]
        mock_services['notification_service'].get_all_notifications.return_value = [sample_notification]
        
        response = client.get("/api/v1/analytics/overview")
        
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "month"
        assert "data" in data
        assert data["data"]["total_clients"] == 1
        assert data["data"]["total_subscriptions"] == 1
        assert data["data"]["total_notifications"] == 1
    
    def test_client_analytics(self, client, sample_client, mock_services):
        """Тест аналитики клиентов."""
        # Настраиваем мок сервиса
        mock_services['client_service'].get_all_clients.return_value = [sample_client]
        
        response = client.get("/api/v1/analytics/clients")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_clients"] == 1
        assert data["active_clients"] == 1
        assert "clients_by_experience" in data
        assert "clients_by_status" in data
    
    def test_subscription_analytics(self, client, sample_subscription, mock_services):
        """Тест аналитики абонементов."""
        # Настраиваем мок сервиса
        mock_services['subscription_service'].get_all_subscriptions.return_value = [sample_subscription]
        
        response = client.get("/api/v1/analytics/subscriptions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_subscriptions"] == 1
        assert data["active_subscriptions"] == 1
        assert "subscriptions_by_type" in data
        assert data["average_subscription_value"] == 9600.0


class TestAPIValidation:
    """Тесты валидации API."""
    
    def test_invalid_client_data(self, client):
        """Тест валидации неверных данных клиента."""
        invalid_data = {
            "name": "",  # Слишком короткое имя
            "phone": "invalid-phone",  # Неверный формат телефона
            "telegram_id": "not_a_number"  # Неверный тип
        }
        
        response = client.post("/api/v1/clients/", json=invalid_data)
        
        assert response.status_code == 422  # Validation Error
    
    def test_invalid_subscription_data(self, client):
        """Тест валидации неверных данных абонемента."""
        invalid_data = {
            "client_id": "",  # Пустой ID клиента
            "classes_total": -1,  # Отрицательное количество
            "price_paid": -100  # Отрицательная цена
        }
        
        response = client.post("/api/v1/subscriptions/", json=invalid_data)
        
        assert response.status_code == 422  # Validation Error
    
    def test_pagination_validation(self, client):
        """Тест валидации параметров пагинации."""
        # Неверная страница
        response = client.get("/api/v1/clients/?page=0")
        assert response.status_code == 422
        
        # Слишком большой лимит
        response = client.get("/api/v1/clients/?limit=1000")
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 