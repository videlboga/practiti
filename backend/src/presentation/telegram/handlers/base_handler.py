"""
🏗️ Базовый обработчик команд Telegram Bot

Родительский класс для всех обработчиков команд.
Принцип CyberKitty: простота превыше всего.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from ....services.protocols.client_service import ClientServiceProtocol

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """
    Базовый класс для всех обработчиков Telegram Bot.
    
    Обеспечивает общую функциональность:
    - Логирование команд
    - Доступ к сервисам
    - Обработка ошибок
    - Получение информации о пользователе
    """
    
    def __init__(self, client_service: ClientServiceProtocol):
        """
        Инициализация обработчика.
        
        Args:
            client_service: Сервис для работы с клиентами
        """
        self.client_service = client_service
        logger.info(f"Инициализирован {self.__class__.__name__}")
    
    async def get_user_info(self, update: Update) -> tuple[int, str, Optional[str]]:
        """
        Получить информацию о пользователе из обновления.
        
        Args:
            update: Telegram обновление
            
        Returns:
            Кортеж (user_id, username, first_name)
        """
        user = update.effective_user
        if not user:
            raise ValueError("Не удалось получить информацию о пользователе")
        
        user_id = user.id
        username = user.username or "неизвестно"
        first_name = user.first_name
        
        return user_id, username, first_name
    
    async def log_command(self, update: Update, command: str) -> None:
        """
        Логировать выполнение команды.
        
        Args:
            update: Telegram обновление
            command: Название команды
        """
        try:
            user_id, username, first_name = await self.get_user_info(update)
            logger.info(
                f"Команда /{command} от пользователя {first_name} "
                f"(@{username}, ID: {user_id})"
            )
        except Exception as e:
            logger.warning(f"Не удалось залогировать команду /{command}: {e}")
    
    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception) -> None:
        """
        Обработать ошибку в команде.
        
        Args:
            update: Telegram обновление
            context: Контекст бота
            error: Возникшая ошибка
        """
        try:
            user_id, username, _ = await self.get_user_info(update)
            logger.error(
                f"Ошибка в команде для пользователя @{username} (ID: {user_id}): {error}",
                exc_info=True
            )
            
            # Отправляем пользователю сообщение об ошибке
            if update.effective_chat:
                await update.effective_chat.send_message(
                    "🚫 Произошла ошибка при обработке команды. "
                    "Попробуйте позже или обратитесь к администратору."
                )
        except Exception as log_error:
            logger.critical(f"Критическая ошибка при обработке ошибки: {log_error}")
    
    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Основной метод обработки команды.
        
        Должен быть реализован в наследниках.
        
        Args:
            update: Telegram обновление
            context: Контекст бота
        """
        pass
    
    async def safe_handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Безопасная обработка команды с обработкой ошибок.
        
        Args:
            update: Telegram обновление
            context: Контекст бота
        """
        try:
            await self.handle(update, context)
        except Exception as e:
            await self.handle_error(update, context, e) 