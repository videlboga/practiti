"""
🧪 Тесты для PostClassService

Тестирование автоматизации после занятий.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from backend.src.services.post_class_service import PostClassService
from backend.src.models.booking import Booking, BookingStatus
from backend.src.models.client import Client, ClientStatus
from backend.src.models.subscription import Subscription, SubscriptionStatus, SubscriptionType


@pytest.fixture
def mock_client_service():
    """Мок сервиса клиентов."""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_subscription_service():
    """Мок сервиса абонементов."""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_notification_service():
    """Мок сервиса уведомлений."""
    service = AsyncMock()
    return service


@pytest.fixture
def post_class_service(mock_client_service, mock_subscription_service, mock_notification_service):
    """Экземпляр PostClassService для тестов."""
    return PostClassService(
        mock_client_service,
        mock_subscription_service,
        mock_notification_service
    )


@pytest.fixture
def sample_client():
    """Тестовый клиент."""
    return Client(
        id="client_123",
        name="Анна Иванова",
        telegram_id=123456789,
        phone="+7-900-123-45-67",
        status=ClientStatus.ACTIVE,
        yoga_experience=True,
        intensity_preference="средняя",
        time_preference="утро"
    )


@pytest.fixture
def sample_booking():
    """Тестовая запись на занятие."""
    # Создаем booking с датой в будущем, затем меняем статус
    booking = Booking(
        id="booking_123",
        client_id="client_123",
        class_date=datetime.now() + timedelta(hours=1),  # Сначала в будущем для валидации
        class_type="хатха",
        status=BookingStatus.SCHEDULED,
        teacher_name="Елена Петрова",
        subscription_id="sub_123"  # Добавляем subscription_id для progress_update
    )
    # Теперь меняем дату и статус для тестирования завершенного занятия
    booking.class_date = datetime.now() - timedelta(hours=1)
    booking.status = BookingStatus.ATTENDED
    return booking


@pytest.fixture
def sample_subscription():
    """Тестовый абонемент."""
    from datetime import date
    return Subscription(
        id="sub_123",
        client_id="client_123",
        type=SubscriptionType.PACKAGE_8,
        total_classes=8,
        used_classes=3,
        status=SubscriptionStatus.ACTIVE,
        start_date=date.today() - timedelta(days=10),
        end_date=date.today() + timedelta(days=20),
        price=7000
    )


@pytest.mark.asyncio
async def test_process_completed_class_success(
    post_class_service, 
    sample_client, 
    sample_booking, 
    sample_subscription,
    mock_client_service,
    mock_subscription_service,
    mock_notification_service
):
    """Тест успешной обработки завершенного занятия."""
    # Настройка моков
    mock_client_service.get_client.return_value = sample_client
    mock_subscription_service.get_subscription.return_value = sample_subscription
    mock_notification_service.send_immediate_notification.return_value = True
    mock_notification_service.create_notification_from_template.return_value = True
    
    # Выполнение
    result = await post_class_service.process_completed_class(sample_booking)
    
    # Проверки
    assert result["success"] is True
    assert result["booking_id"] == sample_booking.id
    assert result["client_id"] == sample_client.id
    assert len(result["actions"]) == 5
    
    # Проверяем, что все действия выполнены
    action_types = [action["action"] for action in result["actions"]]
    expected_actions = [
        "thank_you_message",
        "feedback_request_scheduled", 
        "progress_update",
        "class_recommendations",
        "achievements_check"
    ]
    
    for expected_action in expected_actions:
        assert expected_action in action_types


@pytest.mark.asyncio
async def test_process_completed_class_wrong_status(post_class_service, sample_booking):
    """Тест обработки занятия с неправильным статусом."""
    # Меняем статус на неподходящий
    sample_booking.status = BookingStatus.SCHEDULED
    
    # Выполнение
    result = await post_class_service.process_completed_class(sample_booking)
    
    # Проверки
    assert result["success"] is False
    assert "не помечено как посещенное" in result["error"]


@pytest.mark.asyncio
async def test_process_missed_class_success(
    post_class_service,
    sample_client,
    sample_booking,
    mock_client_service,
    mock_notification_service
):
    """Тест успешной обработки пропущенного занятия."""
    # Настройка
    sample_booking.status = BookingStatus.MISSED
    mock_client_service.get_client.return_value = sample_client
    mock_notification_service.send_immediate_notification.return_value = True
    
    # Выполнение
    result = await post_class_service.process_missed_class(sample_booking)
    
    # Проверки
    assert result["success"] is True
    assert result["booking_id"] == sample_booking.id
    assert result["action"] == "missed_class_message_sent"


@pytest.mark.asyncio
async def test_send_daily_motivation(
    post_class_service,
    sample_client,
    mock_client_service,
    mock_notification_service
):
    """Тест отправки ежедневной мотивации."""
    # Настройка
    mock_client_service.get_active_clients.return_value = [sample_client]
    mock_client_service.get_client.return_value = sample_client
    mock_notification_service.send_immediate_notification.return_value = True
    
    # Выполнение
    sent_count = await post_class_service.send_daily_motivation()
    
    # Проверки
    assert sent_count == 1
    mock_notification_service.send_immediate_notification.assert_called()


@pytest.mark.asyncio
async def test_class_recommendations():
    """Тест получения рекомендаций занятий."""
    service = PostClassService(AsyncMock(), AsyncMock(), AsyncMock())
    
    # Тестируем разные типы занятий
    recommendations = service._get_class_recommendations("хатха")
    assert len(recommendations) >= 1
    assert any("виньяса" in rec.lower() for rec in recommendations)
    
    recommendations = service._get_class_recommendations("виньяса")
    assert len(recommendations) >= 1
    assert any("хатха" in rec.lower() for rec in recommendations)


def test_get_next_week_schedule():
    """Тест получения расписания на неделю."""
    service = PostClassService(AsyncMock(), AsyncMock(), AsyncMock())
    
    schedule = service._get_next_week_schedule()
    
    # Проверяем, что есть расписание на все дни недели
    expected_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    for day in expected_days:
        assert day in schedule
        assert len(schedule[day]) >= 1  # Хотя бы одно занятие в день


def test_get_today_schedule():
    """Тест получения расписания на сегодня."""
    service = PostClassService(AsyncMock(), AsyncMock(), AsyncMock())
    
    schedule = service._get_today_schedule()
    
    # Проверяем, что расписание не пустое
    assert len(schedule) >= 1 