"""
🎫 Протокол репозитория абонементов Practiti

Интерфейс для работы с данными абонементов в любом хранилище.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from ...models.subscription import Subscription, SubscriptionCreateData, SubscriptionUpdateData, SubscriptionStatus


class SubscriptionRepositoryProtocol(ABC):
    """
    Протокол репозитория для работы с абонементами.
    
    Определяет интерфейс для всех операций с данными абонементов.
    """
    
    @abstractmethod
    async def save_subscription(self, data: SubscriptionCreateData) -> Subscription:
        """
        Сохранить новый абонемент.
        
        Args:
            data: Данные для создания абонемента
            
        Returns:
            Созданный абонемент с присвоенным ID
        """
        pass
    
    @abstractmethod
    async def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """
        Получить абонемент по ID.
        
        Args:
            subscription_id: Уникальный ID абонемента
            
        Returns:
            Абонемент или None если не найден
        """
        pass
    
    @abstractmethod
    async def get_subscriptions_by_client_id(self, client_id: str) -> List[Subscription]:
        """
        Получить все абонементы клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Список абонементов клиента
        """
        pass
    
    @abstractmethod
    async def get_active_subscriptions_by_client_id(self, client_id: str) -> List[Subscription]:
        """
        Получить активные абонементы клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Список активных абонементов
        """
        pass
    
    @abstractmethod
    async def update_subscription(self, subscription_id: str, data: SubscriptionUpdateData) -> Optional[Subscription]:
        """
        Обновить данные абонемента.
        
        Args:
            subscription_id: ID абонемента для обновления
            data: Новые данные абонемента
            
        Returns:
            Обновлённый абонемент или None если не найден
        """
        pass
    
    @abstractmethod
    async def delete_subscription(self, subscription_id: str) -> bool:
        """
        Удалить абонемент.
        
        Args:
            subscription_id: ID абонемента для удаления
            
        Returns:
            True если абонемент удалён, False если не найден
        """
        pass
    
    @abstractmethod
    async def list_subscriptions(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[Subscription]:
        """
        Получить список всех абонементов.
        
        Args:
            limit: Максимальное количество абонементов
            offset: Смещение для пагинации
            
        Returns:
            Список абонементов
        """
        pass
    
    @abstractmethod
    async def get_subscriptions_by_status(self, status: SubscriptionStatus) -> List[Subscription]:
        """
        Получить абонементы по статусу.
        
        Args:
            status: Статус абонементов
            
        Returns:
            Список абонементов с указанным статусом
        """
        pass
    
    @abstractmethod
    async def get_expiring_subscriptions(self, days_before: int = 3) -> List[Subscription]:
        """
        Получить абонементы, которые скоро истекут.
        
        Args:
            days_before: За сколько дней до истечения искать
            
        Returns:
            Список истекающих абонементов
        """
        pass
    
    @abstractmethod
    async def count_subscriptions(self) -> int:
        """
        Получить общее количество абонементов.
        
        Returns:
            Количество абонементов
        """
        pass
    
    @abstractmethod
    async def count_subscriptions_by_client(self, client_id: str) -> int:
        """
        Получить количество абонементов клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Количество абонементов клиента
        """
        pass 