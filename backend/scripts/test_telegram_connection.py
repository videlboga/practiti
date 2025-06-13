#!/usr/bin/env python3
"""
🧪 Тест подключения к Telegram API

Проверяет корректность токена и доступность API.
Принцип CyberKitty: простота превыше всего.
"""

import asyncio
import logging
import sys
import os

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from telegram import Bot
from config.settings import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_telegram_connection():
    """
    Тестирует подключение к Telegram API.
    """
    logger.info("🤖 Тестирование подключения к Telegram API...")
    
    try:
        # Получаем конфигурацию
        telegram_config = settings.get_telegram_config()
        
        if telegram_config.bot_token == "fake_token_for_tests":
            logger.error("❌ Токен бота не настроен!")
            logger.info("💡 Создайте .env файл и укажите TELEGRAM_BOT_TOKEN")
            return False
        
        # Создаем бота
        bot = Bot(token=telegram_config.bot_token)
        
        # Получаем информацию о боте
        logger.info("📡 Получение информации о боте...")
        bot_info = await bot.get_me()
        
        logger.info(f"✅ Подключение успешно!")
        logger.info(f"🤖 Имя бота: {bot_info.first_name}")
        logger.info(f"📝 Username: @{bot_info.username}")
        logger.info(f"🆔 ID: {bot_info.id}")
        
        # Проверяем webhook
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            logger.info(f"🔗 Webhook URL: {webhook_info.url}")
        else:
            logger.info("📡 Webhook не настроен (будет использоваться polling)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Telegram API: {e}")
        return False


async def test_send_message():
    """
    Тестирует отправку сообщения администратору.
    """
    logger.info("📤 Тестирование отправки сообщения...")
    
    try:
        telegram_config = settings.get_telegram_config()
        
        if not telegram_config.admin_chat_id:
            logger.warning("⚠️ Admin chat ID не настроен, пропускаем тест отправки")
            return True
        
        bot = Bot(token=telegram_config.bot_token)
        
        test_message = (
            "🧪 **Тест CyberKitty Practiti Backend**\n\n"
            "✅ Telegram Bot успешно подключен!\n"
            "🚀 Готов к работе с йога-студией.\n\n"
            "Принцип CyberKitty: простота превыше всего! 🌟"
        )
        
        await bot.send_message(
            chat_id=telegram_config.admin_chat_id,
            text=test_message,
            parse_mode='Markdown'
        )
        
        logger.info("✅ Тестовое сообщение отправлено администратору!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сообщения: {e}")
        return False


async def main():
    """
    Основная функция тестирования.
    """
    logger.info("🔍 Запуск тестов Telegram API...")
    
    # Тест подключения
    connection_ok = await test_telegram_connection()
    
    if not connection_ok:
        logger.error("💥 Тест подключения провален!")
        return False
    
    # Тест отправки сообщения
    message_ok = await test_send_message()
    
    if connection_ok and message_ok:
        logger.info("🎉 Все тесты прошли успешно!")
        logger.info("🤖 Telegram Bot готов к работе!")
        return True
    else:
        logger.error("💥 Некоторые тесты провалены!")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("👋 Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка: {e}")
        sys.exit(1) 