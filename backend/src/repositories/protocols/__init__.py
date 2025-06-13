"""
🔌 Протоколы репозиториев CyberKitty Practiti

Интерфейсы для всех репозиториев согласно архитектуре.
"""

from .client_repository import ClientRepositoryProtocol

__all__ = [
    "ClientRepositoryProtocol",
] 