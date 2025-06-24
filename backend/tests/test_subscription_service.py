"""
🧪 Тесты для SubscriptionService

Тестирование бизнес-логики управления абонементами.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock

from src.models.subscription import (
    Subscription, SubscriptionCreateData, SubscriptionType, SubscriptionStatus
)
from src.services.subscription_service import SubscriptionService
from src.utils.exceptions import BusinessLogicError


@pytest.fixture
def mock_subscription_repository():
    """Мок репозитория абонементов."""
    return AsyncMock()


@pytest.fixture
def subscription_service(mock_subscription_repository):
    """Сервис абонементов с мок-репозиторием."""
    return SubscriptionService(mock_subscription_repository)


@pytest.fixture
def sample_subscription():
    """Образец абонемента для тестов."""
    return Subscription(
        id="test-subscription-id",
        client_id="test-client-id",
        type=SubscriptionType.PACKAGE_4,
        total_classes=4,
        used_classes=0,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=60),
        price=3200,
        status=SubscriptionStatus.ACTIVE,
        payment_confirmed=True
    )


class TestSubscriptionService:
    """Тесты для SubscriptionService."""
    
    @pytest.mark.asyncio
    async def test_create_subscription_success(self, subscription_service, mock_subscription_repository):
        """Тест успешного создания абонемента."""
        # Arrange
        create_data = SubscriptionCreateData(
            client_id="test-client-id",
            type=SubscriptionType.TRIAL,
            start_date=date.today()
        )
        
        expected_subscription = Subscription(
            client_id="test-client-id",
            type=SubscriptionType.TRIAL,
            total_classes=1,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=60),
            price=500,
            status=SubscriptionStatus.PENDING
        )
        
        mock_subscription_repository.get_active_subscriptions_by_client_id.return_value = []
        mock_subscription_repository.save_subscription.return_value = expected_subscription
        
        # Act
        result = await subscription_service.create_subscription(create_data)
        
        # Assert
        assert result == expected_subscription
        mock_subscription_repository.save_subscription.assert_called_once_with(create_data)
    
    @pytest.mark.asyncio
    async def test_create_multiple_active_subscriptions_allowed(
        self, subscription_service, mock_subscription_repository, sample_subscription
    ):
        """Теперь допускается создание нескольких активных абонементов."""

        create_data = SubscriptionCreateData(
            client_id="test-client-id",
            type=SubscriptionType.TRIAL
        )

        # Репозиторий сообщает, что уже есть активный
        mock_subscription_repository.get_active_subscriptions_by_client_id.return_value = [sample_subscription]

        # Ожидаем, что сервис всё равно вызывает save_subscription
        mock_subscription_repository.save_subscription.return_value = sample_subscription

        result = await subscription_service.create_subscription(create_data)

        assert result == sample_subscription
        mock_subscription_repository.save_subscription.assert_called_once_with(create_data)
    
    @pytest.mark.asyncio
    async def test_get_subscription_success(self, subscription_service, mock_subscription_repository, sample_subscription):
        """Тест успешного получения абонемента."""
        # Arrange
        mock_subscription_repository.get_subscription_by_id.return_value = sample_subscription
        
        # Act
        result = await subscription_service.get_subscription("test-subscription-id")
        
        # Assert
        assert result == sample_subscription
        mock_subscription_repository.get_subscription_by_id.assert_called_once_with("test-subscription-id")
    
    @pytest.mark.asyncio
    async def test_get_subscription_not_found(self, subscription_service, mock_subscription_repository):
        """Тест получения несуществующего абонемента."""
        # Arrange
        mock_subscription_repository.get_subscription_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(BusinessLogicError, match="Абонемент с ID test-id не найден"):
            await subscription_service.get_subscription("test-id")
    
    @pytest.mark.asyncio
    async def test_use_class_success(self, subscription_service, mock_subscription_repository, sample_subscription):
        """Тест успешного списания занятия."""
        # Arrange
        subscription_data = sample_subscription.model_dump()
        subscription_data['used_classes'] = 1
        updated_subscription = Subscription(**subscription_data)
        
        mock_subscription_repository.get_subscription_by_id.return_value = sample_subscription
        mock_subscription_repository.update_subscription.return_value = updated_subscription
        
        # Act
        result = await subscription_service.use_class("test-subscription-id")
        
        # Assert
        assert result.used_classes == 1
        assert result.remaining_classes == 3
    
    @pytest.mark.asyncio
    async def test_use_class_on_inactive_subscription_fails(
        self, subscription_service, mock_subscription_repository
    ):
        """Тест списания занятия с неактивного абонемента."""
        # Arrange
        inactive_subscription = Subscription(
            id="test-id",
            client_id="test-client-id",
            type=SubscriptionType.TRIAL,
            total_classes=1,
            used_classes=0,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=60),
            price=500,
            status=SubscriptionStatus.PENDING,  # Неактивный
            payment_confirmed=False
        )
        
        mock_subscription_repository.get_subscription_by_id.return_value = inactive_subscription
        
        # Act & Assert
        with pytest.raises(BusinessLogicError, match="неактивен"):
            await subscription_service.use_class("test-id")
    
    def test_get_subscription_price(self, subscription_service):
        """Тест получения цены абонемента."""
        assert subscription_service.get_subscription_price(SubscriptionType.TRIAL) == 500
        assert subscription_service.get_subscription_price(SubscriptionType.SINGLE) == 1100
        assert subscription_service.get_subscription_price(SubscriptionType.PACKAGE_4) == 3200
        assert subscription_service.get_subscription_price(SubscriptionType.UNLIMITED) == 10800
    
    def test_calculate_subscription_end_date(self, subscription_service):
        """Тест расчета даты окончания абонемента."""
        start_date = date(2024, 1, 1)
        
        # Пробный и разовое, пакетные – 60 дней
        assert subscription_service.calculate_subscription_end_date(
            SubscriptionType.TRIAL, start_date
        ) == date(2024, 3, 1)
        
        assert subscription_service.calculate_subscription_end_date(
            SubscriptionType.SINGLE, start_date
        ) == date(2024, 3, 1)
        
        assert subscription_service.calculate_subscription_end_date(
            SubscriptionType.PACKAGE_4, start_date
        ) == date(2024, 3, 1)
    
    def test_get_subscription_info(self, subscription_service):
        """Тест получения информации об абонементе."""
        info = subscription_service.get_subscription_info(SubscriptionType.PACKAGE_8)
        
        assert info["type"] == "package_8"
        assert info["price"] == 7000
        assert info["classes"] == 8
        assert info["duration_days"] == 60
        assert "8 занятий" in info["description"] 