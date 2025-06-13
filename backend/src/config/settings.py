"""
⚙️ Настройки конфигурации CyberKitty Practiti

Централизованное управление настройками.
Принцип CyberKitty: простота превыше всего.
"""

import os
from dataclasses import dataclass
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


@dataclass
class TelegramConfig:
    """Конфигурация Telegram Bot."""
    
    bot_token: str
    admin_chat_id: Optional[int] = None
    webhook_url: Optional[str] = None
    webhook_port: int = 8080


@dataclass
class GoogleSheetsConfig:
    """Конфигурация Google Sheets."""
    
    spreadsheet_id: str
    credentials_path: str
    scopes: list[str] = None
    
    def __post_init__(self):
        if self.scopes is None:
            self.scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.readonly'
            ]


@dataclass
class APIConfig:
    """Конфигурация FastAPI."""
    
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000"]


class Settings(BaseSettings):
    """
    Основные настройки приложения.
    
    Загружает конфигурацию из переменных окружения.
    """
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # Общие настройки
    app_name: str = "CyberKitty Practiti Backend"
    debug: bool = False
    
    # Telegram Bot
    telegram_bot_token: str = "fake_token_for_tests"
    telegram_admin_chat_id: Optional[int] = None
    telegram_webhook_url: Optional[str] = None
    telegram_webhook_port: int = 8080
    
    # Google Sheets
    google_sheets_id: str = "fake_sheet_id_for_tests"
    google_credentials_path: str = "credentials.json"
    
    # API
    api_host: str = "localhost"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:3000"
    
    # Логирование
    log_level: str = "INFO"
    
    def get_telegram_config(self) -> TelegramConfig:
        """Получить конфигурацию Telegram Bot."""
        return TelegramConfig(
            bot_token=self.telegram_bot_token,
            admin_chat_id=self.telegram_admin_chat_id,
            webhook_url=self.telegram_webhook_url,
            webhook_port=self.telegram_webhook_port
        )
    
    def get_google_sheets_config(self) -> GoogleSheetsConfig:
        """Получить конфигурацию Google Sheets."""
        return GoogleSheetsConfig(
            spreadsheet_id=self.google_sheets_id,
            credentials_path=self.google_credentials_path
        )
    
    def get_api_config(self) -> APIConfig:
        """Получить конфигурацию API."""
        return APIConfig(
            host=self.api_host,
            port=self.api_port,
            debug=self.debug,
            cors_origins=self.api_cors_origins.split(",")
        )


# Глобальный экземпляр настроек
settings = Settings() 