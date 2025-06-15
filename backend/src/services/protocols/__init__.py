"""
🔌 Протоколы сервисов Practiti

Интерфейсы для всех сервисов согласно архитектуре.
"""

from .client_service import ClientServiceProtocol
from .subscription_service import SubscriptionServiceProtocol
from .notification_service import NotificationServiceProtocol

__all__ = [
    "ClientServiceProtocol",
    "SubscriptionServiceProtocol",
    "NotificationServiceProtocol",
] 