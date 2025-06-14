"""
🧪 Простые тесты для проверки настройки тестовой среды
"""

import pytest
import os
from unittest.mock import patch

# Устанавливаем тестовые переменные окружения перед импортом
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
os.environ["GOOGLE_SPREADSHEET_ID"] = "test_spreadsheet"
os.environ["SECRET_KEY"] = "test_secret"

from src.config.settings import get_test_settings


def test_test_settings():
    """Тест тестовых настроек."""
    settings = get_test_settings()
    
    # Проверяем, что настройки загружаются (значения могут быть из env переменных)
    assert settings.telegram_bot_token is not None
    assert settings.google_sheets_id is not None  # Исправлено имя поля
    assert settings.secret_key is not None
    assert settings.debug is True
    assert settings.environment == "testing"


def test_basic_math():
    """Базовый тест для проверки работы pytest."""
    assert 2 + 2 == 4
    assert "hello" + " world" == "hello world"


@pytest.mark.asyncio
async def test_async_function():
    """Тест асинхронной функции."""
    async def async_add(a, b):
        return a + b
    
    result = await async_add(3, 4)
    assert result == 7 