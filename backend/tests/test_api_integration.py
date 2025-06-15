"""
🧪 Интеграционные тесты API

Простые тесты для проверки работы API endpoints без моков.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta

from backend.src.api.main import create_app


@pytest.fixture
def client():
    """Тестовый клиент FastAPI."""
    app = create_app()
    return TestClient(app)


class TestAPIIntegration:
    """Интеграционные тесты API."""
    
    def test_health_check(self, client):
        """Тест health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "practiti-admin-api"
        assert data["version"] == "1.0.0"
    
    def test_clients_list_empty(self, client):
        """Тест получения пустого списка клиентов."""
        response = client.get("/api/v1/clients/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["limit"] == 20
        assert len(data["items"]) == 0
    
    def test_subscriptions_list_empty(self, client):
        """Тест получения пустого списка абонементов."""
        response = client.get("/api/v1/subscriptions/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["limit"] == 20
        assert len(data["items"]) == 0
    
    def test_notifications_list_empty(self, client):
        """Тест получения пустого списка уведомлений."""
        response = client.get("/api/v1/notifications/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["limit"] == 20
        assert len(data["items"]) == 0
    
    def test_analytics_overview(self, client):
        """Тест получения общей аналитики."""
        response = client.get("/api/v1/analytics/overview")
        
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "data" in data
        assert "generated_at" in data
    
    def test_analytics_clients(self, client):
        """Тест получения аналитики клиентов."""
        response = client.get("/api/v1/analytics/clients")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_clients"] == 0
        assert data["active_clients"] == 0
        assert data["new_clients_this_month"] == 0
    
    def test_create_client_invalid_data(self, client):
        """Тест создания клиента с невалидными данными."""
        invalid_data = {
            "name": "",  # Пустое имя
            "phone": "invalid",  # Невалидный телефон
            "telegram_id": "not_a_number"  # Не число
        }
        
        response = client.post("/api/v1/clients/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_nonexistent_client(self, client):
        """Тест получения несуществующего клиента."""
        response = client.get("/api/v1/clients/nonexistent-id")
        assert response.status_code == 404
    
    def test_get_nonexistent_subscription(self, client):
        """Тест получения несуществующего абонемента."""
        response = client.get("/api/v1/subscriptions/nonexistent-id")
        assert response.status_code == 404
    
    def test_get_nonexistent_notification(self, client):
        """Тест получения несуществующего уведомления."""
        response = client.get("/api/v1/notifications/nonexistent-id")
        assert response.status_code == 404 