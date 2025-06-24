"""
🎫 Протокол сервиса абонементов Practiti

Интерфейс для работы с абонементами клиентов йога-студии.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from ...models.subscription import Subscription, SubscriptionCreateData, SubscriptionUpdateData, SubscriptionType


class SubscriptionServiceProtocol(ABC):
    """
    Протокол сервиса для работы с абонементами.
    
    Определяет интерфейс для всех операций с абонементами клиентов.
    """
    
    @abstractmethod
    async def create_subscription(self, data: SubscriptionCreateData) -> Subscription:
        """
        Создать новый абонемент.
        
        Args:
            data: Данные для создания абонемента
            
        Returns:
            Созданный абонемент
            
        Raises:
            ValidationError: При некорректных данных
            BusinessLogicError: При нарушении бизнес-правил
        """
        pass
    
    @abstractmethod
    async def get_subscription(self, subscription_id: str) -> Subscription:
        """
        Получить абонемент по ID.
        
        Args:
            subscription_id: ID абонемента
            
        Returns:
            Абонемент
            
        Raises:
            BusinessLogicError: Если абонемент не найден
        """
        pass
    
    @abstractmethod
    async def get_all_subscriptions(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Subscription]:
        """
        Получить все абонементы.
        
        Args:
            limit: Максимальное количество абонементов
            offset: Смещение для пагинации
            
        Returns:
            Список всех абонементов
        """
        pass
    
    @abstractmethod
    async def get_client_subscriptions(self, client_id: str) -> List[Subscription]:
        """
        Получить все абонементы клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Список абонементов клиента
        """
        pass
    
    @abstractmethod
    async def get_active_subscription(self, client_id: str) -> Optional[Subscription]:
        """
        Получить активный абонемент клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Активный абонемент или None
        """
        pass
    
    @abstractmethod
    async def use_class(self, subscription_id: str) -> Subscription:
        """
        Списать одно занятие с абонемента.
        
        Args:
            subscription_id: ID абонемента
            
        Returns:
            Обновленный абонемент
            
        Raises:
            BusinessLogicError: Если нельзя списать занятие
        """
        pass
    
    @abstractmethod
    async def confirm_payment(self, subscription_id: str) -> Subscription:
        """
        Подтвердить оплату абонемента.
        
        Args:
            subscription_id: ID абонемента
            
        Returns:
            Обновленный абонемент
        """
        pass
    
    @abstractmethod
    async def extend_subscription(self, subscription_id: str, additional_days: int) -> Subscription:
        """
        Продлить срок действия абонемента.
        
        Args:
            subscription_id: ID абонемента
            additional_days: Количество дней для продления
            
        Returns:
            Обновленный абонемент
        """
        pass
    
    @abstractmethod
    async def suspend_subscription(self, subscription_id: str) -> Subscription:
        """
        Приостановить абонемент.
        
        Args:
            subscription_id: ID абонемента
            
        Returns:
            Обновленный абонемент
        """
        pass
    
    @abstractmethod
    async def resume_subscription(self, subscription_id: str) -> Subscription:
        """
        Возобновить приостановленный абонемент.
        
        Args:
            subscription_id: ID абонемента
            
        Returns:
            Обновленный абонемент
        """
        pass
    
    @abstractmethod
    async def update_subscription_status(self) -> int:
        """
        Обновить статусы всех абонементов (expired, exhausted).
        
        Проверяет все абонементы и обновляет их статусы согласно
        текущей дате и количеству оставшихся занятий.
        
        Returns:
            Количество обновленных абонементов
        """
        pass
    
    @abstractmethod
    async def get_subscription_statistics(self, client_id: str) -> dict:
        """
        Получить статистику по абонементам клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Словарь со статистикой
        """
        pass
    
    @abstractmethod
    def get_subscription_price(self, subscription_type: SubscriptionType) -> int:
        """
        Получить цену абонемента по типу.
        
        Args:
            subscription_type: Тип абонемента
            
        Returns:
            Цена в рублях
        """
        pass
    
    @abstractmethod
    def calculate_subscription_end_date(self, subscription_type: SubscriptionType, start_date: date) -> date:
        """
        Рассчитать дату окончания абонемента.
        
        Args:
            subscription_type: Тип абонемента
            start_date: Дата начала
            
        Returns:
            Дата окончания
        """
        pass
    
    @abstractmethod
    async def cancel_subscription(self, subscription_id: str, reason: str | None = None) -> Subscription:
        """
        Отменить (аннулировать) абонемент.

        Args:
            subscription_id: ID абонемента
            reason: Причина отмены (опционально, для логов)

        Returns:
            Обновленный абонемент со статусом CANCELLED
        """
        pass
    
    @abstractmethod
    async def freeze_subscription(self, subscription_id: str, days: int, reason: str | None = None) -> Subscription:
        """
        Заморозить (приостановить) абонемент на указанное количество дней.

        Args:
            subscription_id: ID абонемента
            days: Количество дней заморозки
            reason: Причина (опционально)

        Returns:
            Обновленный абонемент
        """
        pass 