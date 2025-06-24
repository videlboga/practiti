#!/usr/bin/env python3
"""
🚀 Главный модуль Practiti Backend

Точка входа для запуска Telegram Bot и API.
Принцип CyberKitty: простота превыше всего.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from .config.settings import settings
from .presentation.telegram.bot import PrakritiTelegramBot
from .services.client_service import ClientService
from .services.subscription_service import SubscriptionService
from .services.notification_service import NotificationService
from .services.scheduler_service import SchedulerService
from .services.telegram_sender_service import TelegramSenderService
from .services.post_class_service import PostClassService
from .services.feedback_service import FeedbackService

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/backend.log', mode='a', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


class PrakritiApplication:
    """
    Основное приложение Practiti.
    
    Управляет запуском и остановкой всех компонентов:
    - Telegram Bot
    - REST API (в будущем)
    - Фоновые задачи (в будущем)
    """
    
    def __init__(self):
        """Инициализация приложения."""
        self.telegram_bot: Optional[PrakritiTelegramBot] = None
        self.client_service: Optional[ClientService] = None
        self.subscription_service: Optional[SubscriptionService] = None
        self.notification_service: Optional[NotificationService] = None
        self.scheduler_service: Optional[SchedulerService] = None
        self.telegram_sender: Optional[TelegramSenderService] = None
        self.post_class_service: Optional[PostClassService] = None
        self.feedback_service: Optional[FeedbackService] = None
        self.is_running = False
        
        logger.info("PrakritiApplication инициализировано")
    
    async def initialize(self) -> None:
        """
        Инициализация всех компонентов приложения.
        """
        logger.info("Инициализация компонентов приложения...")
        
        try:
            # Временно используем репозитории в памяти для тестирования
            logger.info("Инициализация временных репозиториев в памяти...")
            from .repositories.in_memory_client_repository import InMemoryClientRepository
            from .repositories.in_memory_subscription_repository import InMemorySubscriptionRepository
            from .repositories.in_memory_notification_repository import InMemoryNotificationRepository
            
            client_repository = InMemoryClientRepository()
            subscription_repository = InMemorySubscriptionRepository()
            notification_repository = InMemoryNotificationRepository()
            
            # Инициализируем сервисы
            logger.info("Инициализация ClientService...")
            self.client_service = ClientService(client_repository)
            
            logger.info("Инициализация SubscriptionService...")
            self.subscription_service = SubscriptionService(subscription_repository)
            
            logger.info("Инициализация TelegramSenderService...")
            self.telegram_sender = TelegramSenderService()
            
            logger.info("Инициализация NotificationService...")
            self.notification_service = NotificationService(
                notification_repository, 
                self.client_service, 
                self.subscription_service,
                self.telegram_sender
            )
            
            logger.info("Инициализация FeedbackService...")
            self.feedback_service = FeedbackService(self.notification_service)
            
            logger.info("Инициализация PostClassService...")
            self.post_class_service = PostClassService(
                self.client_service,
                self.subscription_service,
                self.notification_service
            )
            
            logger.info("Инициализация SchedulerService...")
            self.scheduler_service = SchedulerService(
                self.client_service,
                self.subscription_service,
                self.notification_service
            )
            
            # Инициализируем Telegram Bot
            logger.info("Инициализация Telegram Bot...")
            telegram_config = settings.get_telegram_config()
            self.telegram_bot = PrakritiTelegramBot(
                telegram_config, 
                self.client_service, 
                self.subscription_service
            )
            await self.telegram_bot.initialize()
            
            logger.info("Все компоненты успешно инициализированы")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            raise
    
    async def start(self) -> None:
        """
        Запуск приложения.
        """
        if not self.telegram_bot:
            await self.initialize()
        
        logger.info("🚀 Запуск Practiti Backend...")
        
        self.is_running = True
        
        try:
            # Запускаем планировщик
            if self.scheduler_service:
                logger.info("Запуск планировщика задач...")
                await self.scheduler_service.start()
            
            # Запускаем Telegram Bot в polling режиме
            if self.telegram_bot:
                await self.telegram_bot.start_polling()
        except Exception as e:
            logger.error(f"Ошибка запуска приложения: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """
        Остановка приложения.
        """
        logger.info("Остановка Practiti Backend...")
        
        self.is_running = False
        
        # Останавливаем планировщик
        if self.scheduler_service:
            logger.info("Остановка планировщика задач...")
            await self.scheduler_service.stop()
        
        # Останавливаем Telegram Bot
        if self.telegram_bot:
            await self.telegram_bot.stop()
        
        logger.info("Приложение остановлено")
    
    def setup_signal_handlers(self) -> None:
        """
        Настройка обработчиков сигналов для корректного завершения.
        """
        def signal_handler(signum, frame):
            logger.info(f"Получен сигнал {signum}, завершение работы...")
            if self.is_running:
                # Создаем новый event loop для остановки
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.stop())
                loop.close()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """
    Основная функция запуска.
    """
    logger.info("🤖 Practiti Backend запускается...")
    logger.info("Андрей, принцип: простота превыше всего! 🚀")
    logger.info("⚠️  Используется временный репозиторий в памяти для тестирования")
    
    # Создаем приложение
    app = PrakritiApplication()
    
    # Настраиваем обработчики сигналов
    app.setup_signal_handlers()
    
    try:
        # Запускаем приложение
        await app.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершение работы...")
        await app.stop()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        await app.stop()
        sys.exit(1)


if __name__ == "__main__":
    # Создаем папку для логов
    import os
    os.makedirs('logs', exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Practiti Backend завершен пользователем")
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка при запуске: {e}")
        sys.exit(1) 