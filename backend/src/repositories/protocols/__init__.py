"""
🔌 Протоколы репозиториев Practiti

Интерфейсы для всех репозиториев согласно архитектуре.
"""

from .client_repository import ClientRepositoryProtocol
from .subscription_repository import SubscriptionRepositoryProtocol

__all__ = [
    "ClientRepositoryProtocol",
    "SubscriptionRepositoryProtocol",
] 