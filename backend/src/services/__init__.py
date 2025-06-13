"""
🏗️ Сервисы CyberKitty Practiti

Бизнес-логика приложения согласно архитектуре.
"""

from .client_service import ClientService
from .protocols import ClientServiceProtocol

__all__ = [
    "ClientService",
    "ClientServiceProtocol",
]
