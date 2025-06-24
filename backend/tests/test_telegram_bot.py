"""
🧪 Тесты для Telegram Bot

Тестирует базовую функциональность бота.
Принцип CyberKitty: простота превыше всего.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from src.config.settings import TelegramConfig
from src.presentation.telegram.bot import PrakritiTelegramBot
from src.presentation.telegram.handlers.command_handlers import CommandHandlers
from src.services.client_service import ClientService
from src.models.client import Client, ClientStatus


class TestCommandHandlers:
    """Тесты обработчиков команд."""
    
    @pytest.fixture
    def mock_client_service(self):
        """Мок ClientService для тестов."""
        return AsyncMock(spec=ClientService)
    
    @pytest.fixture
    def command_handlers(self, mock_client_service):
        """Экземпляр CommandHandlers для тестов."""
        return CommandHandlers(mock_client_service)
    
    @pytest.fixture
    def mock_update(self):
        """Мок Telegram Update."""
        user = Mock(spec=User)
        user.id = 123456789
        user.username = "test_user"
        user.first_name = "Тест"
        
        chat = Mock(spec=Chat)
        chat.id = 123456789
        chat.send_message = AsyncMock()
        
        message = Mock(spec=Message)
        message.text = "/start"
        
        update = Mock(spec=Update)
        update.effective_user = user
        update.effective_chat = chat
        update.message = message
        
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Мок Context."""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        return context
    
    @pytest.mark.asyncio
    async def test_start_command_new_user(self, command_handlers, mock_client_service, mock_update, mock_context):
        """Тест команды /start для нового пользователя."""
        # Arrange
        mock_client_service.get_client_by_telegram_id.return_value = None
        
        # Act
        await command_handlers.start_command(mock_update, mock_context)
        
        # Assert
        mock_client_service.get_client_by_telegram_id.assert_called_once_with(123456789)
        mock_update.effective_chat.send_message.assert_called_once()
        
        # Проверяем, что сообщение содержит приветствие
        call_args = mock_update.effective_chat.send_message.call_args[0][0]
        assert "Добро пожаловать" in call_args
        assert "Practiti" in call_args
    
    @pytest.mark.asyncio
    async def test_help_command_new_user(self, command_handlers, mock_client_service, mock_update, mock_context):
        """Тест команды /help для нового пользователя."""
        # Arrange
        mock_client_service.get_client_by_telegram_id.return_value = None
        
        # Act
        await command_handlers.help_command(mock_update, mock_context)
        
        # Assert
        mock_update.effective_chat.send_message.assert_called_once()
        
        # Проверяем, что сообщение содержит команды для незарегистрированного пользователя
        call_args = mock_update.effective_chat.send_message.call_args
        message_text = call_args[0][0]
        assert "/register" in message_text
        assert "регистрация" in message_text
    
    @pytest.mark.asyncio
    async def test_info_command(self, command_handlers, mock_client_service, mock_update, mock_context):
        """Тест команды /info."""
        # Act
        await command_handlers.info_command(mock_update, mock_context)
        
        # Assert
        mock_update.effective_chat.send_message.assert_called_once()
        
        # Проверяем, что сообщение содержит информацию о студии
        call_args = mock_update.effective_chat.send_message.call_args
        message_text = call_args[0][0]
        assert "Practiti" in message_text
        assert "йога" in message_text.lower()


class TestPrakritiTelegramBot:
    """Тесты основного класса Telegram Bot."""
    
    @pytest.fixture
    def telegram_config(self):
        """Конфигурация для тестов."""
        return TelegramConfig(
            bot_token="fake_token",
            admin_chat_id=123456789
        )
    
    @pytest.fixture
    def mock_client_service(self):
        """Мок ClientService для тестов."""
        return AsyncMock(spec=ClientService)
    
    @pytest.fixture
    def mock_subscription_service(self):
        """Мок SubscriptionService для тестов."""
        return AsyncMock()
    
    def test_bot_initialization(self, telegram_config, mock_client_service, mock_subscription_service):
        """Тест инициализации бота."""
        # Act
        bot = PrakritiTelegramBot(telegram_config, mock_client_service, mock_subscription_service)
        
        # Assert
        assert bot.config == telegram_config
        assert bot.client_service == mock_client_service
        assert bot.subscription_service == mock_subscription_service
        assert bot.application is None
        assert isinstance(bot.command_handlers, CommandHandlers) 