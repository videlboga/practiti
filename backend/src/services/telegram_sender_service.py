"""
📱 Сервис отправки Telegram сообщений

Отвечает за отправку уведомлений через Telegram Bot API.
Интегрируется с NotificationService для автоматических напоминаний.
"""

import logging
from typing import Optional, Dict, Any
from telegram import Bot
from telegram.error import TelegramError

from ..models.client import Client
from ..models.notification import Notification
from ..config.settings import settings

logger = logging.getLogger(__name__)


class TelegramSenderService:
    """
    Сервис для отправки уведомлений через Telegram.
    
    Обеспечивает:
    - Отправку текстовых сообщений
    - Форматирование уведомлений
    - Обработку ошибок Telegram API
    - Логирование отправок
    """
    
    def __init__(self):
        """Инициализация сервиса отправки Telegram сообщений."""
        self._bot: Optional[Bot] = None
        self._is_enabled = False
        
        # Разрешаем реальные запросы ТОЛЬКО в production.
        if settings.environment != "production":
            logger.info("TelegramSenderService запущен в непроизводственном окружении — отправка сообщений отключена")
            return

        # Production: инициализируем бота, если указан валидный токен
        telegram_config = settings.get_telegram_config()
        if telegram_config.bot_token and telegram_config.bot_token != "fake_token_for_tests":
            try:
                self._bot = Bot(token=telegram_config.bot_token)
                self._is_enabled = True
                logger.info("TelegramSenderService инициализирован с реальным токеном")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать Telegram Bot: {e}")
                self._is_enabled = False
        else:
            logger.info("TelegramSenderService инициализирован без рабочего токена — отправка сообщений отключена")
            self._is_enabled = False
    
    async def send_notification_to_client(
        self, 
        client: Client, 
        notification: Notification
    ) -> tuple[bool, Optional[int], Optional[str]]:
        """
        Отправить уведомление клиенту через Telegram.
        
        Args:
            client: Клиент-получатель
            notification: Уведомление для отправки
            
        Returns:
            Кортеж (успех, message_id, ошибка)
        """
        if not self._is_enabled:
            logger.info(f"Telegram отправка отключена, имитация отправки уведомления {notification.id}")
            return True, None, None
        
        if not client.telegram_id:
            error_msg = f"У клиента {client.id} нет Telegram ID"
            logger.warning(error_msg)
            return False, None, error_msg
        
        try:
            # Форматируем сообщение
            formatted_message = self._format_notification_message(notification)
            
            # Отправляем сообщение
            message = await self._bot.send_message(
                chat_id=client.telegram_id,
                text=formatted_message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Уведомление {notification.id} отправлено клиенту {client.id} (message_id: {message.message_id})")
            return True, message.message_id, None
            
        except TelegramError as e:
            error_msg = f"Ошибка Telegram API: {e}"
            logger.error(f"Не удалось отправить уведомление {notification.id}: {error_msg}")
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {e}"
            logger.error(f"Критическая ошибка при отправке уведомления {notification.id}: {error_msg}")
            return False, None, error_msg
    
    async def send_custom_message(
        self, 
        telegram_id: int, 
        message: str,
        parse_mode: str = 'Markdown'
    ) -> tuple[bool, Optional[int], Optional[str]]:
        """
        Отправить произвольное сообщение по Telegram ID.
        
        Args:
            telegram_id: Telegram ID получателя
            message: Текст сообщения
            parse_mode: Режим парсинга (Markdown, HTML)
            
        Returns:
            Кортеж (успех, message_id, ошибка)
        """
        if not self._is_enabled:
            logger.info(f"Telegram отправка отключена, имитация отправки сообщения в {telegram_id}")
            return True, None, None
        
        try:
            sent_message = await self._bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode=parse_mode
            )
            
            logger.info(f"Сообщение отправлено в {telegram_id} (message_id: {sent_message.message_id})")
            return True, sent_message.message_id, None
            
        except TelegramError as e:
            error_msg = f"Ошибка Telegram API: {e}"
            logger.error(f"Не удалось отправить сообщение в {telegram_id}: {error_msg}")
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {e}"
            logger.error(f"Критическая ошибка при отправке сообщения в {telegram_id}: {error_msg}")
            return False, None, error_msg
    
    def _format_notification_message(self, notification: Notification) -> str:
        """
        Форматировать уведомление для отправки в Telegram.
        
        Args:
            notification: Уведомление для форматирования
            
        Returns:
            Отформатированное сообщение
        """
        # Базовое форматирование
        message_parts = []
        
        # Заголовок с эмодзи в зависимости от типа
        title_emoji = self._get_emoji_for_notification_type(notification.type)
        message_parts.append(f"{title_emoji} **{notification.title}**")
        
        # Основное сообщение
        message_parts.append("")
        message_parts.append(notification.message)
        
        # Дополнительная информация из метаданных
        if notification.metadata:
            additional_info = self._format_metadata(notification.metadata)
            if additional_info:
                message_parts.append("")
                message_parts.append(additional_info)
        
        # Подпись студии
        message_parts.append("")
        message_parts.append("---")
        message_parts.append("🧘‍♀️ *Practiti - Йога Студия*")
        
        return "\n".join(message_parts)
    
    def _get_emoji_for_notification_type(self, notification_type) -> str:
        """Получить эмодзи для типа уведомления."""
        emoji_map = {
            'class_reminder': '⏰',
            'subscription_expiry': '⚠️',
            'schedule_reminder': '📅',
            'welcome': '🌟',
            'registration_complete': '✅',
            'subscription_purchased': '🎉',
            'general_info': 'ℹ️',
            'promotion': '🎁',
            'class_cancelled': '❌',
            'schedule_change': '🔄'
        }
        
        return emoji_map.get(notification_type.value if hasattr(notification_type, 'value') else str(notification_type), 'ℹ️')
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Форматировать метаданные уведомления.
        
        Args:
            metadata: Метаданные уведомления
            
        Returns:
            Отформатированная строка с дополнительной информацией
        """
        formatted_parts = []
        
        # Дата занятия
        if 'class_date' in metadata:
            try:
                from datetime import datetime
                class_date = datetime.fromisoformat(metadata['class_date'])
                formatted_parts.append(f"📅 Дата: {class_date.strftime('%d.%m.%Y в %H:%M')}")
            except:
                pass
        
        # Тип занятия
        if 'class_type' in metadata:
            formatted_parts.append(f"🧘‍♀️ Тип: {metadata['class_type']}")
        
        # Дата истечения абонемента
        if 'expiry_date' in metadata:
            try:
                from datetime import datetime
                expiry_date = datetime.fromisoformat(metadata['expiry_date'])
                formatted_parts.append(f"📅 Истекает: {expiry_date.strftime('%d.%m.%Y')}")
            except:
                pass
        
        # Оставшиеся занятия
        if 'remaining_classes' in metadata:
            formatted_parts.append(f"🎫 Осталось занятий: {metadata['remaining_classes']}")
        
        # Цена
        if 'price' in metadata:
            formatted_parts.append(f"💰 Стоимость: {metadata['price']} ₽")
        
        return "\n".join(formatted_parts)
    
    def is_enabled(self) -> bool:
        """Проверить, включена ли отправка через Telegram."""
        return self._is_enabled
    
    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """
        Проверить соединение с Telegram API.
        
        Returns:
            Кортеж (успех, ошибка)
        """
        if not self._is_enabled:
            return False, "Telegram отправка отключена"
        
        try:
            bot_info = await self._bot.get_me()
            logger.info(f"Соединение с Telegram API успешно. Bot: @{bot_info.username}")
            return True, None
            
        except Exception as e:
            error_msg = f"Ошибка соединения с Telegram API: {e}"
            logger.error(error_msg)
            return False, error_msg 