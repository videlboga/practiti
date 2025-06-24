"""
📢 Тесты для NotificationService

Проверяем всю бизнес-логику работы с уведомлениями.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from backend.src.models.notification import (
    NotificationCreateData, NotificationType, NotificationStatus, NotificationPriority
)
from backend.src.models.client import Client, ClientCreateData
from backend.src.services.notification_service import NotificationService
from backend.src.repositories.in_memory_notification_repository import InMemoryNotificationRepository
from backend.src.utils.exceptions import BusinessLogicError


@pytest.fixture
def notification_repository():
    """Фикстура репозитория уведомлений."""
    return InMemoryNotificationRepository()


@pytest.fixture
def mock_client_service():
    """Мок клиентского сервиса."""
    service = AsyncMock()
    
    # Настраиваем мок клиента
    test_client = Client(
        id="test_client_123",
        telegram_id=123456789,
        name="Тестовый Клиент",
        phone="+79001234567",
        yoga_experience=True,
        intensity_preference="средняя",
        time_preference="вечер"
    )
    service.get_client.return_value = test_client
    
    return service


@pytest.fixture
def mock_subscription_service():
    """Мок сервиса абонементов."""
    return AsyncMock()


@pytest.fixture
def mock_telegram_sender():
    """Мок Telegram sender service."""
    sender = AsyncMock()
    # Мокируем успешную отправку
    sender.send_notification_to_client.return_value = (True, 12345, None)
    return sender


@pytest.fixture
def notification_service(notification_repository, mock_client_service, mock_subscription_service, mock_telegram_sender):
    """Фикстура сервиса уведомлений."""
    return NotificationService(
        notification_repository=notification_repository,
        client_service=mock_client_service,
        subscription_service=mock_subscription_service,
        telegram_sender=mock_telegram_sender
    )


@pytest.mark.asyncio
async def test_create_notification_success(notification_service):
    """Тест успешного создания уведомления."""
    # Arrange
    notification_data = NotificationCreateData(
        client_id="test_client_123",
        type=NotificationType.WELCOME_MESSAGE,
        title="Добро пожаловать!",
        message="Добро пожаловать в Practiti!",
        priority=NotificationPriority.NORMAL
    )
    
    # Act
    notification = await notification_service.create_notification(notification_data)
    
    # Assert
    assert notification.client_id == "test_client_123"
    assert notification.type == NotificationType.WELCOME_MESSAGE
    assert notification.title == "Добро пожаловать!"
    assert notification.status == NotificationStatus.PENDING
    assert notification.priority == NotificationPriority.NORMAL


@pytest.mark.asyncio
async def test_create_notification_client_not_found(notification_service, mock_client_service):
    """Тест создания уведомления для несуществующего клиента."""
    # Arrange
    mock_client_service.get_client.side_effect = BusinessLogicError("Клиент не найден")
    
    notification_data = NotificationCreateData(
        client_id="nonexistent_client",
        type=NotificationType.WELCOME_MESSAGE,
        title="Добро пожаловать!",
        message="Добро пожаловать в Practiti!"
    )
    
    # Act & Assert
    with pytest.raises(BusinessLogicError, match="Клиент с ID nonexistent_client не найден"):
        await notification_service.create_notification(notification_data)


@pytest.mark.asyncio
async def test_create_notification_from_template_success(notification_service):
    """Тест создания уведомления из шаблона."""
    # Arrange
    template_data = {
        'client_name': 'Тестовый Клиент'
    }
    
    # Act
    notification = await notification_service.create_notification_from_template(
        client_id="test_client_123",
        notification_type=NotificationType.WELCOME_MESSAGE,
        template_data=template_data
    )
    
    # Assert
    assert notification.client_id == "test_client_123"
    assert notification.type == NotificationType.WELCOME_MESSAGE
    assert "Тестовый Клиент" in notification.message
    assert notification.status == NotificationStatus.PENDING


@pytest.mark.asyncio
async def test_create_notification_from_template_missing_data(notification_service):
    """Тест создания уведомления из шаблона с недостающими данными."""
    # Arrange
    template_data = {}  # Пустые данные
    
    # Act & Assert
    with pytest.raises(BusinessLogicError, match="Ошибка форматирования шаблона"):
        await notification_service.create_notification_from_template(
            client_id="test_client_123",
            notification_type=NotificationType.WELCOME_MESSAGE,
            template_data=template_data
        )


@pytest.mark.asyncio
async def test_get_notification_success(notification_service):
    """Тест получения уведомления по ID."""
    # Arrange
    notification_data = NotificationCreateData(
        client_id="test_client_123",
        type=NotificationType.WELCOME_MESSAGE,
        title="Тест",
        message="Тестовое сообщение"
    )
    created_notification = await notification_service.create_notification(notification_data)
    
    # Act
    notification = await notification_service.get_notification(created_notification.id)
    
    # Assert
    assert notification.id == created_notification.id
    assert notification.title == "Тест"


@pytest.mark.asyncio
async def test_get_notification_not_found(notification_service):
    """Тест получения несуществующего уведомления."""
    # Act & Assert
    with pytest.raises(BusinessLogicError, match="Уведомление с ID nonexistent не найдено"):
        await notification_service.get_notification("nonexistent")


@pytest.mark.asyncio
async def test_send_notification_success(notification_service):
    """Тест отправки уведомления."""
    # Arrange
    notification_data = NotificationCreateData(
        client_id="test_client_123",
        type=NotificationType.WELCOME_MESSAGE,
        title="Тест",
        message="Тестовое сообщение"
    )
    notification = await notification_service.create_notification(notification_data)
    
    # Act
    result = await notification_service.send_notification(notification.id)
    
    # Assert
    assert result is True
    
    # Проверяем, что статус изменился
    updated_notification = await notification_service.get_notification(notification.id)
    assert updated_notification.status == NotificationStatus.SENT
    assert updated_notification.sent_at is not None


@pytest.mark.asyncio
async def test_send_immediate_notification_success(notification_service):
    """Тест немедленной отправки уведомления."""
    # Arrange
    template_data = {'client_name': 'Тестовый Клиент'}
    
    # Act
    result = await notification_service.send_immediate_notification(
        client_id="test_client_123",
        notification_type=NotificationType.WELCOME_MESSAGE,
        template_data=template_data
    )
    
    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_mark_as_delivered(notification_service):
    """Тест пометки уведомления как доставленного."""
    # Arrange
    notification_data = NotificationCreateData(
        client_id="test_client_123",
        type=NotificationType.WELCOME_MESSAGE,
        title="Тест",
        message="Тестовое сообщение"
    )
    notification = await notification_service.create_notification(notification_data)
    await notification_service.send_notification(notification.id)
    
    # Act
    updated_notification = await notification_service.mark_as_delivered(notification.id)
    
    # Assert
    assert updated_notification.status == NotificationStatus.DELIVERED
    assert updated_notification.delivered_at is not None


@pytest.mark.asyncio
async def test_mark_as_failed(notification_service):
    """Тест пометки уведомления как неудачного."""
    # Arrange
    notification_data = NotificationCreateData(
        client_id="test_client_123",
        type=NotificationType.WELCOME_MESSAGE,
        title="Тест",
        message="Тестовое сообщение"
    )
    notification = await notification_service.create_notification(notification_data)
    
    # Act
    updated_notification = await notification_service.mark_as_failed(
        notification.id, 
        "Ошибка отправки"
    )
    
    # Assert
    assert updated_notification.status == NotificationStatus.FAILED
    assert updated_notification.retry_count == 1


@pytest.mark.asyncio
async def test_cancel_notification(notification_service):
    """Тест отмены уведомления."""
    # Arrange
    notification_data = NotificationCreateData(
        client_id="test_client_123",
        type=NotificationType.WELCOME_MESSAGE,
        title="Тест",
        message="Тестовое сообщение"
    )
    notification = await notification_service.create_notification(notification_data)
    
    # Act
    updated_notification = await notification_service.cancel_notification(notification.id)
    
    # Assert
    assert updated_notification.status == NotificationStatus.CANCELLED


@pytest.mark.asyncio
async def test_get_client_notifications(notification_service):
    """Тест получения уведомлений клиента."""
    # Arrange
    client_id = "test_client_123"
    
    # Создаем несколько уведомлений
    for i in range(3):
        notification_data = NotificationCreateData(
            client_id=client_id,
            type=NotificationType.WELCOME_MESSAGE,
            title=f"Тест {i}",
            message=f"Тестовое сообщение {i}"
        )
        await notification_service.create_notification(notification_data)
    
    # Act
    notifications = await notification_service.get_client_notifications(client_id)
    
    # Assert
    assert len(notifications) == 3
    assert all(n.client_id == client_id for n in notifications)


@pytest.mark.asyncio
async def test_get_notification_statistics_client(notification_service):
    """Тест получения статистики по клиенту."""
    # Arrange
    client_id = "test_client_123"
    
    # Создаем уведомления разных типов и статусов
    notification_data = NotificationCreateData(
        client_id=client_id,
        type=NotificationType.WELCOME_MESSAGE,
        title="Тест 1",
        message="Сообщение 1"
    )
    notification1 = await notification_service.create_notification(notification_data)
    await notification_service.send_notification(notification1.id)
    
    notification_data2 = NotificationCreateData(
        client_id=client_id,
        type=NotificationType.GENERAL_INFO,
        title="Тест 2",
        message="Сообщение 2"
    )
    await notification_service.create_notification(notification_data2)
    
    # Act
    stats = await notification_service.get_notification_statistics(client_id)
    
    # Assert
    assert stats['client_id'] == client_id
    assert stats['total_notifications'] == 2
    assert 'sent' in stats['by_status']
    assert 'pending' in stats['by_status']
    assert len(stats['recent_notifications']) == 2


@pytest.mark.asyncio
async def test_get_notification_statistics_general(notification_service):
    """Тест получения общей статистики."""
    # Arrange
    notification_data = NotificationCreateData(
        client_id="test_client_123",
        type=NotificationType.WELCOME_MESSAGE,
        title="Тест",
        message="Сообщение"
    )
    await notification_service.create_notification(notification_data)
    
    # Act
    stats = await notification_service.get_notification_statistics()
    
    # Assert
    assert 'total_notifications' in stats
    assert 'by_status' in stats
    assert 'by_type' in stats
    assert 'system_health' in stats
    assert stats['total_notifications'] > 0


@pytest.mark.asyncio
async def test_send_welcome_notification(notification_service):
    """Тест отправки приветственного уведомления."""
    # Act
    result = await notification_service.send_welcome_notification(
        client_id="test_client_123",
        client_name="Тестовый Клиент"
    )
    
    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_send_registration_complete_notification(notification_service):
    """Тест отправки уведомления о завершении регистрации."""
    # Act
    result = await notification_service.send_registration_complete_notification(
        client_id="test_client_123",
        client_name="Тестовый Клиент"
    )
    
    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_send_subscription_purchased_notification(notification_service):
    """Тест отправки уведомления о покупке абонемента."""
    # Act
    result = await notification_service.send_subscription_purchased_notification(
        client_id="test_client_123",
        client_name="Тестовый Клиент",
        subscription_type="PACKAGE_8",
        total_classes=8,
        end_date="31.12.2024",
        price=7000
    )
    
    # Assert
    assert result is True 