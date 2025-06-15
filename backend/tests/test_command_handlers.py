"""
🧪 Тесты для обработчиков команд Telegram Bot

Тестируем информационные команды Session B8.
Принцип CyberKitty: простота превыше всего.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, User, Chat
from telegram.ext import ContextTypes

from backend.src.presentation.telegram.handlers.command_handlers import CommandHandlers
from backend.src.services.protocols.client_service import ClientServiceProtocol


@pytest.fixture
def mock_client_service():
    """Мок сервиса клиентов."""
    service = AsyncMock(spec=ClientServiceProtocol)
    return service


@pytest.fixture
def command_handlers(mock_client_service):
    """Создание экземпляра CommandHandlers для тестов."""
    return CommandHandlers(mock_client_service)


@pytest.fixture
def mock_update():
    """Мок Telegram Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.effective_user.first_name = "Test"
    
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.send_message = AsyncMock()
    
    return update


@pytest.fixture
def mock_context():
    """Мок Telegram Context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    return context


@pytest.mark.asyncio
async def test_address_command_success(command_handlers, mock_update, mock_context):
    """Тест успешного выполнения команды /address."""
    
    # Act
    await command_handlers.address_command(mock_update, mock_context)
    
    # Assert
    mock_update.effective_chat.send_message.assert_called_once()
    call_args = mock_update.effective_chat.send_message.call_args
    
    # Проверяем, что сообщение содержит ключевые элементы
    message_text = call_args[0][0]  # Первый позиционный аргумент
    
    assert "📍" in message_text
    assert "Practiti" in message_text
    assert "Москва" in message_text
    assert "Режим работы" in message_text
    assert "Контакты" in message_text
    assert "Как добраться" in message_text
    
    # Проверяем, что используется Markdown
    assert call_args[1]["parse_mode"] == "Markdown"


@pytest.mark.asyncio
async def test_address_command_handles_error(command_handlers, mock_update, mock_context):
    """Тест обработки ошибки в команде /address."""
    
    # Arrange
    mock_update.effective_chat.send_message.side_effect = [Exception("Test error"), None]
    
    # Act & Assert - не должно выбрасывать исключение
    await command_handlers.address_command(mock_update, mock_context)
    
    # Проверяем, что было 2 вызова: основное сообщение (с ошибкой) + сообщение об ошибке
    assert mock_update.effective_chat.send_message.call_count == 2


@pytest.mark.asyncio
async def test_faq_command_success(command_handlers, mock_update, mock_context):
    """Тест успешного выполнения команды /faq."""
    
    # Act
    await command_handlers.faq_command(mock_update, mock_context)
    
    # Assert
    mock_update.effective_chat.send_message.assert_called_once()
    call_args = mock_update.effective_chat.send_message.call_args
    
    # Проверяем, что сообщение содержит ключевые элементы
    message_text = call_args[0][0]  # Первый позиционный аргумент
    
    assert "❓" in message_text
    assert "Часто задаваемые вопросы" in message_text
    assert "О занятиях" in message_text
    assert "Об абонементах" in message_text
    assert "О записи" in message_text
    assert "опыт" in message_text
    assert "абонемент" in message_text
    
    # Проверяем, что используется Markdown
    assert call_args[1]["parse_mode"] == "Markdown"


@pytest.mark.asyncio
async def test_contact_command_success(command_handlers, mock_update, mock_context):
    """Тест успешного выполнения команды /contact."""
    
    # Act
    await command_handlers.contact_command(mock_update, mock_context)
    
    # Assert
    mock_update.effective_chat.send_message.assert_called_once()
    call_args = mock_update.effective_chat.send_message.call_args
    
    # Проверяем, что сообщение содержит ключевые элементы
    message_text = call_args[0][0]  # Первый позиционный аргумент
    
    assert "📞" in message_text
    assert "администратор" in message_text
    assert "Телефон" in message_text
    assert "WhatsApp" in message_text
    assert "Email" in message_text
    assert "+7 (999) 123-45-67" in message_text
    
    # Проверяем, что используется Markdown
    assert call_args[1]["parse_mode"] == "Markdown"


@pytest.mark.asyncio
async def test_prices_command_success(command_handlers, mock_update, mock_context):
    """Тест успешного выполнения команды /prices."""
    
    # Act
    await command_handlers.prices_command(mock_update, mock_context)
    
    # Assert
    mock_update.effective_chat.send_message.assert_called_once()
    call_args = mock_update.effective_chat.send_message.call_args
    
    # Проверяем, что сообщение содержит ключевые элементы
    message_text = call_args[0][0]  # Первый позиционный аргумент
    
    assert "💰" in message_text
    assert "Цены на абонементы" in message_text
    assert "Разовое занятие" in message_text
    assert "1 500 ₽" in message_text
    assert "Абонемент 4 занятия" in message_text
    assert "Индивидуальные занятия" in message_text
    assert "Способы оплаты" in message_text
    
    # Проверяем, что используется Markdown
    assert call_args[1]["parse_mode"] == "Markdown"


@pytest.mark.asyncio
async def test_schedule_command_success(command_handlers, mock_update, mock_context):
    """Тест успешного выполнения команды /schedule."""
    
    # Act
    await command_handlers.schedule_command(mock_update, mock_context)
    
    # Assert
    mock_update.effective_chat.send_message.assert_called_once()
    call_args = mock_update.effective_chat.send_message.call_args
    
    # Проверяем, что сообщение содержит ключевые элементы
    message_text = call_args[0][0]  # Первый позиционный аргумент
    
    assert "📅" in message_text
    assert "Расписание занятий" in message_text
    assert "ПОНЕДЕЛЬНИК" in message_text
    assert "Хатха-йога" in message_text
    assert "Виньяса-флоу" in message_text
    assert "08:00" in message_text
    assert "Уровни сложности" in message_text
    assert "Запись на занятия" in message_text
    
    # Проверяем, что используется Markdown
    assert call_args[1]["parse_mode"] == "Markdown" 