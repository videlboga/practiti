"""
🧪 Тесты для FeedbackService

Тестирование сервиса обратной связи.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from backend.src.services.feedback_service import FeedbackService
from backend.src.models.feedback import (
    Feedback, FeedbackCreateData, FeedbackUpdateData,
    FeedbackType, FeedbackStatus
)
from backend.src.models.client import Client, ClientStatus
from backend.src.models.booking import Booking, BookingStatus


@pytest.fixture
def mock_notification_service():
    """Мок сервиса уведомлений."""
    service = AsyncMock()
    service.send_immediate_notification.return_value = True
    return service


@pytest.fixture
def feedback_service(mock_notification_service):
    """Экземпляр FeedbackService для тестов."""
    return FeedbackService(mock_notification_service)


@pytest.fixture
def sample_client():
    """Тестовый клиент."""
    return Client(
        id="client_123",
        name="Мария Петрова",
        telegram_id=987654321,
        phone="+7-900-987-65-43",
        status=ClientStatus.ACTIVE,
        yoga_experience=True,
        intensity_preference="высокая",
        time_preference="вечер"
    )


@pytest.fixture
def sample_booking():
    """Тестовая запись на занятие."""
    # Создаем booking с датой в будущем, затем меняем
    booking = Booking(
        id="booking_456",
        client_id="client_123",
        class_date=datetime.now() + timedelta(hours=1),
        class_type="виньяса",
        status=BookingStatus.SCHEDULED,
        teacher_name="Анна Сидорова"
    )
    # Меняем для тестирования завершенного занятия
    booking.class_date = datetime.now() - timedelta(hours=2)
    booking.status = BookingStatus.ATTENDED
    return booking


@pytest.mark.asyncio
async def test_create_feedback_request(feedback_service, sample_client, sample_booking):
    """Тест создания запроса обратной связи."""
    # Выполнение
    feedback = await feedback_service.create_feedback_request(
        sample_client, 
        sample_booking,
        FeedbackType.POST_CLASS
    )
    
    # Проверки
    assert feedback.client_id == sample_client.id
    assert feedback.booking_id == sample_booking.id
    assert feedback.type == FeedbackType.POST_CLASS
    assert feedback.status == FeedbackStatus.PENDING
    assert feedback.metadata['class_type'] == sample_booking.class_type
    assert feedback.metadata['teacher_name'] == sample_booking.teacher_name
    
    # Проверяем, что feedback сохранен в хранилище
    stored_feedback = await feedback_service.get_feedback(feedback.id)
    assert stored_feedback is not None
    assert stored_feedback.id == feedback.id


@pytest.mark.asyncio
async def test_send_feedback_request_post_class(
    feedback_service, 
    sample_client, 
    sample_booking,
    mock_notification_service
):
    """Тест отправки запроса обратной связи после занятия."""
    # Создаем feedback
    feedback = await feedback_service.create_feedback_request(
        sample_client, 
        sample_booking,
        FeedbackType.POST_CLASS
    )
    
    # Выполнение
    result = await feedback_service.send_feedback_request(feedback, sample_client)
    
    # Проверки
    assert result is True
    mock_notification_service.send_immediate_notification.assert_called_once()
    
    # Проверяем параметры вызова
    call_args = mock_notification_service.send_immediate_notification.call_args
    assert call_args[1]['client_id'] == sample_client.id
    template_data = call_args[1]['template_data']
    assert template_data['feedback_type'] == 'post_class'
    assert template_data['feedback_id'] == feedback.id
    assert 'Спасибо за участие' in template_data['message']


@pytest.mark.asyncio
async def test_send_feedback_request_general(
    feedback_service, 
    sample_client, 
    sample_booking,
    mock_notification_service
):
    """Тест отправки общего запроса обратной связи."""
    # Создаем feedback
    feedback = await feedback_service.create_feedback_request(
        sample_client, 
        sample_booking,
        FeedbackType.GENERAL
    )
    
    # Выполнение
    result = await feedback_service.send_feedback_request(feedback, sample_client)
    
    # Проверки
    assert result is True
    
    # Проверяем параметры вызова
    call_args = mock_notification_service.send_immediate_notification.call_args
    template_data = call_args[1]['template_data']
    assert template_data['feedback_type'] == 'general'
    assert 'Поделитесь своими впечатлениями' in template_data['message']


@pytest.mark.asyncio
async def test_submit_feedback(feedback_service, sample_client, sample_booking):
    """Тест принятия обратной связи от клиента."""
    # Создаем feedback
    feedback = await feedback_service.create_feedback_request(
        sample_client, 
        sample_booking
    )
    
    # Данные для обновления
    update_data = FeedbackUpdateData(
        rating=5,
        comment="Отличное занятие! Очень понравилось!",
        class_rating=5,
        teacher_rating=5,
        studio_rating=4,
        would_recommend=True,
        difficulty_level="нормально",
        favorite_part="Расслабление в конце",
        improvement_suggestions="Больше времени на разминку"
    )
    
    # Выполнение
    updated_feedback = await feedback_service.submit_feedback(feedback.id, update_data)
    
    # Проверки
    assert updated_feedback.rating == 5
    assert updated_feedback.comment == "Отличное занятие! Очень понравилось!"
    assert updated_feedback.class_rating == 5
    assert updated_feedback.teacher_rating == 5
    assert updated_feedback.studio_rating == 4
    assert updated_feedback.would_recommend is True
    assert updated_feedback.difficulty_level == "нормально"
    assert updated_feedback.favorite_part == "Расслабление в конце"
    assert updated_feedback.improvement_suggestions == "Больше времени на разминку"
    assert updated_feedback.status == FeedbackStatus.SUBMITTED
    assert updated_feedback.submitted_at is not None


@pytest.mark.asyncio
async def test_submit_feedback_not_found(feedback_service):
    """Тест принятия обратной связи с несуществующим ID."""
    update_data = FeedbackUpdateData(rating=5, comment="Тест")
    
    # Выполнение и проверка исключения
    with pytest.raises(ValueError, match="не найдена"):
        await feedback_service.submit_feedback("nonexistent_id", update_data)


@pytest.mark.asyncio
async def test_get_client_feedback(feedback_service, sample_client, sample_booking):
    """Тест получения всей обратной связи клиента."""
    # Создаем несколько feedback для клиента
    feedback1 = await feedback_service.create_feedback_request(
        sample_client, sample_booking, FeedbackType.POST_CLASS
    )
    feedback2 = await feedback_service.create_feedback_request(
        sample_client, sample_booking, FeedbackType.GENERAL
    )
    
    # Выполнение
    client_feedback = await feedback_service.get_client_feedback(sample_client.id)
    
    # Проверки
    assert len(client_feedback) == 2
    feedback_ids = [f.id for f in client_feedback]
    assert feedback1.id in feedback_ids
    assert feedback2.id in feedback_ids


@pytest.mark.asyncio
async def test_get_booking_feedback(feedback_service, sample_client, sample_booking):
    """Тест получения обратной связи по занятию."""
    # Создаем feedback для занятия
    feedback = await feedback_service.create_feedback_request(
        sample_client, sample_booking
    )
    
    # Выполнение
    booking_feedback = await feedback_service.get_booking_feedback(sample_booking.id)
    
    # Проверки
    assert booking_feedback is not None
    assert booking_feedback.id == feedback.id
    assert booking_feedback.booking_id == sample_booking.id


@pytest.mark.asyncio
async def test_get_feedback_summary_empty(feedback_service):
    """Тест получения сводки при отсутствии обратной связи."""
    # Выполнение
    summary = await feedback_service.get_feedback_summary()
    
    # Проверки
    assert summary.total_feedback == 0
    assert summary.average_rating is None
    assert summary.positive_feedback_percentage == 0.0


@pytest.mark.asyncio
async def test_get_feedback_summary_with_data(feedback_service, sample_client, sample_booking):
    """Тест получения сводки с данными."""
    # Создаем и заполняем feedback
    feedback1 = await feedback_service.create_feedback_request(sample_client, sample_booking)
    feedback2 = await feedback_service.create_feedback_request(sample_client, sample_booking)
    
    # Заполняем данными
    await feedback_service.submit_feedback(feedback1.id, FeedbackUpdateData(
        rating=5, comment="Отлично!"
    ))
    await feedback_service.submit_feedback(feedback2.id, FeedbackUpdateData(
        rating=3, comment="Нормально"
    ))
    
    # Выполнение
    summary = await feedback_service.get_feedback_summary()
    
    # Проверки
    assert summary.total_feedback == 2
    assert summary.average_rating == 4.0  # (5 + 3) / 2
    assert summary.positive_feedback_percentage == 50.0  # 1 из 2 положительных (>=4)
    assert summary.rating_distribution[5] == 1
    assert summary.rating_distribution[3] == 1


def test_feedback_templates(feedback_service, sample_client):
    """Тест шаблонов сообщений обратной связи."""
    # Создаем mock feedback
    feedback = Feedback(
        client_id=sample_client.id,
        type=FeedbackType.POST_CLASS,
        metadata={'class_type': 'хатха'}
    )
    
    # Тест post-class шаблона
    template = feedback_service._get_post_class_feedback_template(feedback, sample_client)
    assert template['client_name'] == sample_client.name
    assert template['feedback_type'] == 'post_class'
    assert template['class_type'] == 'хатха'
    assert 'Спасибо за участие' in template['message']
    
    # Тест general шаблона
    feedback.type = FeedbackType.GENERAL
    template = feedback_service._get_general_feedback_template(feedback, sample_client)
    assert template['feedback_type'] == 'general'
    assert 'Поделитесь своими впечатлениями' in template['message']


@pytest.mark.asyncio
async def test_feedback_properties(feedback_service, sample_client, sample_booking):
    """Тест свойств модели Feedback."""
    # Создаем и заполняем feedback
    feedback = await feedback_service.create_feedback_request(sample_client, sample_booking)
    
    # Заполняем детальными оценками
    await feedback_service.submit_feedback(feedback.id, FeedbackUpdateData(
        rating=4,
        class_rating=5,
        teacher_rating=4,
        studio_rating=3,
        comment="Хорошее занятие"
    ))
    
    updated_feedback = await feedback_service.get_feedback(feedback.id)
    
    # Проверяем свойства
    assert updated_feedback.overall_rating == 4.0  # (4 + 5 + 4 + 3) / 4
    assert updated_feedback.is_positive is True  # >= 4.0
    assert updated_feedback.is_complete is True  # есть rating и comment 