"""
🎫 Временный репозиторий абонементов в памяти для тестирования

Используется для отладки без подключения к Google Sheets.
"""

from typing import List, Optional, Dict
from datetime import date, datetime, timedelta

from ..models.subscription import (
    Subscription, SubscriptionCreateData, SubscriptionUpdateData, 
    SubscriptionStatus, SubscriptionType
)
from ..repositories.protocols.subscription_repository import SubscriptionRepositoryProtocol
from ..utils.logger import get_logger

logger = get_logger(__name__)


class InMemorySubscriptionRepository(SubscriptionRepositoryProtocol):
    """
    Временный репозиторий абонементов в памяти.
    
    Используется для тестирования без подключения к Google Sheets.
    """
    
    def __init__(self):
        """Инициализация репозитория."""
        self._subscriptions: Dict[str, Subscription] = {}
        self._client_index: Dict[str, List[str]] = {}  # client_id -> [subscription_ids]
        
        logger.info("InMemorySubscriptionRepository инициализирован")
    
    async def save_subscription(self, data: SubscriptionCreateData) -> Subscription:
        """
        Сохранить новый абонемент.
        
        Args:
            data: Данные для создания абонемента
            
        Returns:
            Созданный абонемент
        """
        # Получаем цену и конечную дату по типу
        price = self._get_subscription_price(data.type)
        total_classes = self._get_subscription_classes(data.type)
        end_date = self._calculate_end_date(data.type, data.start_date)
        
        subscription = Subscription(
            client_id=data.client_id,
            type=data.type,
            total_classes=total_classes,
            start_date=data.start_date,
            end_date=end_date,
            price=price,
            status=SubscriptionStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Сохраняем абонемент
        self._subscriptions[subscription.id] = subscription
        
        # Обновляем индекс клиентов
        if data.client_id not in self._client_index:
            self._client_index[data.client_id] = []
        self._client_index[data.client_id].append(subscription.id)
        
        logger.info(f"Абонемент {subscription.type.value} сохранен в памяти с ID: {subscription.id}")
        return subscription
    
    async def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """
        Получить абонемент по ID.
        
        Args:
            subscription_id: ID абонемента
            
        Returns:
            Абонемент или None
        """
        return self._subscriptions.get(subscription_id)
    
    async def get_subscriptions_by_client_id(self, client_id: str) -> List[Subscription]:
        """
        Получить все абонементы клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Список абонементов клиента
        """
        subscription_ids = self._client_index.get(client_id, [])
        return [self._subscriptions[sid] for sid in subscription_ids if sid in self._subscriptions]
    
    async def get_active_subscriptions_by_client_id(self, client_id: str) -> List[Subscription]:
        """
        Получить активные абонементы клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Список активных абонементов
        """
        all_subscriptions = await self.get_subscriptions_by_client_id(client_id)
        return [sub for sub in all_subscriptions if sub.is_active]
    
    async def update_subscription(self, subscription_id: str, data: SubscriptionUpdateData) -> Optional[Subscription]:
        """
        Обновить данные абонемента.
        
        Args:
            subscription_id: ID абонемента
            data: Данные для обновления
            
        Returns:
            Обновленный абонемент или None
        """
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None
        
        # Обновляем поля
        if data.status is not None:
            subscription.status = data.status
        if data.used_classes is not None:
            subscription.used_classes = data.used_classes
        if data.payment_confirmed is not None:
            subscription.payment_confirmed = data.payment_confirmed
            if data.payment_confirmed:
                subscription.payment_confirmed_at = datetime.now()
        if data.end_date is not None:
            subscription.end_date = data.end_date
        if data.remaining_classes is not None:
            # Изменяем used_classes исходя из оставшихся занятий
            subscription.used_classes = subscription.total_classes - data.remaining_classes
        if getattr(data, 'total_classes', None) is not None:  # type: ignore[attr-defined]
            subscription.total_classes = data.total_classes  # type: ignore[attr-defined]
        if getattr(data, 'type', None) is not None:  # type: ignore[attr-defined]
            subscription.type = data.type  # type: ignore[attr-defined]
            # total_classes пересчитываем только если явно передан или остаётся прежним
        
        logger.info(f"Абонемент {subscription_id} обновлен в памяти")
        return subscription
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """
        Удалить абонемент.
        
        Args:
            subscription_id: ID абонемента для удаления
            
        Returns:
            True если абонемент удалён, False если не найден
        """
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return False
        
        # Удаляем из основного хранилища
        del self._subscriptions[subscription_id]
        
        # Удаляем из индекса клиентов
        if subscription.client_id in self._client_index:
            if subscription_id in self._client_index[subscription.client_id]:
                self._client_index[subscription.client_id].remove(subscription_id)
        
        logger.info(f"Абонемент {subscription_id} удален из памяти")
        return True
    
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
        subscriptions = list(self._subscriptions.values())
        
        if offset:
            subscriptions = subscriptions[offset:]
        if limit:
            subscriptions = subscriptions[:limit]
            
        return subscriptions
    
    async def get_subscriptions_by_status(self, status: SubscriptionStatus) -> List[Subscription]:
        """
        Получить абонементы по статусу.
        
        Args:
            status: Статус абонементов
            
        Returns:
            Список абонементов с указанным статусом
        """
        return [sub for sub in self._subscriptions.values() if sub.status == status]
    
    async def get_expiring_subscriptions(self, days_before: int = 3) -> List[Subscription]:
        """
        Получить абонементы, которые скоро истекут.
        
        Args:
            days_before: За сколько дней до истечения искать
            
        Returns:
            Список истекающих абонементов
        """
        target_date = date.today() + timedelta(days=days_before)
        
        return [
            sub for sub in self._subscriptions.values()
            if sub.status == SubscriptionStatus.ACTIVE and sub.end_date <= target_date
        ]
    
    async def count_subscriptions(self) -> int:
        """
        Получить общее количество абонементов.
        
        Returns:
            Количество абонементов
        """
        return len(self._subscriptions)
    
    async def count_subscriptions_by_client(self, client_id: str) -> int:
        """
        Получить количество абонементов клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Количество абонементов клиента
        """
        return len(self._client_index.get(client_id, []))
    
    def clear_all(self) -> int:
        """
        Очистить все данные (для тестирования).
        
        Returns:
            Количество удаленных записей
        """
        count = len(self._subscriptions)
        self._subscriptions.clear()
        self._client_index.clear()
        
        logger.info(f"Очищено {count} абонементов из памяти")
        return count
    
    def _get_subscription_price(self, subscription_type: SubscriptionType) -> int:
        """Получить цену абонемента по типу."""
        prices = {
            SubscriptionType.TRIAL: 500,
            SubscriptionType.SINGLE: 1100,
            SubscriptionType.PACKAGE_4: 3200,
            SubscriptionType.PACKAGE_8: 7000,
            SubscriptionType.PACKAGE_12: 9000,
            SubscriptionType.UNLIMITED: 10800,
        }
        return prices[subscription_type]
    
    def _get_subscription_classes(self, subscription_type: SubscriptionType) -> int:
        """Получить количество занятий по типу абонемента."""
        classes = {
            SubscriptionType.TRIAL: 1,
            SubscriptionType.SINGLE: 1,
            SubscriptionType.PACKAGE_4: 4,
            SubscriptionType.PACKAGE_8: 8,
            SubscriptionType.PACKAGE_12: 12,
            SubscriptionType.UNLIMITED: 999,  # Безлимитный
        }
        return classes[subscription_type]
    
    def _calculate_end_date(self, subscription_type: SubscriptionType, start_date: date) -> date:
        """Рассчитать дату окончания абонемента."""
        if subscription_type == SubscriptionType.TRIAL:
            return start_date + timedelta(days=14)
        elif subscription_type == SubscriptionType.SINGLE:
            return start_date + timedelta(days=1)  # Разовое занятие действует один день
        else:
            return start_date + timedelta(days=30)  # Все остальные - 30 дней 