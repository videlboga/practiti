"""
🔌 Протоколы репозиториев Practiti

Интерфейсы для всех репозиториев согласно архитектуре.
"""

from .client_repository import ClientRepositoryProtocol
from .subscription_repository import SubscriptionRepositoryProtocol
from .notification_repository import NotificationRepositoryProtocol

__all__ = [
    "ClientRepositoryProtocol",
    "SubscriptionRepositoryProtocol",
    "NotificationRepositoryProtocol",
] 