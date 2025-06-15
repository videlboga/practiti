"""
📢 Временный репозиторий уведомлений в памяти для тестирования

Используется для отладки без подключения к Google Sheets.
"""

from typing import List, Optional, Dict
from datetime import datetime

from ..models.notification import (
    Notification, NotificationCreateData, NotificationUpdateData, 
    NotificationStatus, NotificationType, NotificationPriority
)
from ..repositories.protocols.notification_repository import NotificationRepositoryProtocol
from ..utils.logger import get_logger

logger = get_logger(__name__)


class InMemoryNotificationRepository(NotificationRepositoryProtocol):
    """
    Временный репозиторий уведомлений в памяти.
    
    Используется для тестирования без подключения к Google Sheets.
    """
    
    def __init__(self):
        """Инициализация репозитория."""
        self._notifications: Dict[str, Notification] = {}
        self._client_index: Dict[str, List[str]] = {}  # client_id -> [notification_ids]
        
        logger.info("InMemoryNotificationRepository инициализирован")
    
    async def save_notification(self, data: NotificationCreateData) -> Notification:
        """
        Сохранить новое уведомление.
        
        Args:
            data: Данные для создания уведомления
            
        Returns:
            Созданное уведомление
        """
        notification = Notification(
            client_id=data.client_id,
            type=data.type,
            title=data.title,
            message=data.message,
            priority=data.priority,
            scheduled_at=data.scheduled_at,
            metadata=data.metadata,
            created_at=datetime.now()
        )
        
        # Сохраняем уведомление
        self._notifications[notification.id] = notification
        
        # Обновляем индекс клиентов
        if data.client_id not in self._client_index:
            self._client_index[data.client_id] = []
        self._client_index[data.client_id].append(notification.id)
        
        logger.info(f"Уведомление {notification.type.value} сохранено в памяти с ID: {notification.id}")
        return notification
    
    async def get_notification_by_id(self, notification_id: str) -> Optional[Notification]:
        """
        Получить уведомление по ID.
        
        Args:
            notification_id: ID уведомления
            
        Returns:
            Уведомление или None
        """
        return self._notifications.get(notification_id)
    
    async def get_notifications_by_client_id(
        self, 
        client_id: str, 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Notification]:
        """
        Получить уведомления клиента.
        
        Args:
            client_id: ID клиента
            limit: Максимальное количество уведомлений
            offset: Смещение для пагинации
            
        Returns:
            Список уведомлений клиента
        """
        notification_ids = self._client_index.get(client_id, [])
        notifications = [self._notifications[nid] for nid in notification_ids if nid in self._notifications]
        
        # Сортируем по дате создания (новые первыми)
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        
        if offset:
            notifications = notifications[offset:]
        if limit:
            notifications = notifications[:limit]
            
        return notifications
    
    async def get_notifications_by_status(self, status: NotificationStatus) -> List[Notification]:
        """
        Получить уведомления по статусу.
        
        Args:
            status: Статус уведомлений
            
        Returns:
            Список уведомлений с указанным статусом
        """
        return [n for n in self._notifications.values() if n.status == status]
    
    async def get_notifications_by_type(self, notification_type: NotificationType) -> List[Notification]:
        """
        Получить уведомления по типу.
        
        Args:
            notification_type: Тип уведомлений
            
        Returns:
            Список уведомлений указанного типа
        """
        return [n for n in self._notifications.values() if n.type == notification_type]
    
    async def get_scheduled_notifications(self, before_time: datetime) -> List[Notification]:
        """
        Получить запланированные уведомления до указанного времени.
        
        Args:
            before_time: Время, до которого искать уведомления
            
        Returns:
            Список запланированных уведомлений
        """
        return [
            n for n in self._notifications.values()
            if (n.status == NotificationStatus.PENDING and 
                n.scheduled_at is not None and 
                n.scheduled_at <= before_time)
        ]
    
    async def get_failed_notifications_for_retry(self) -> List[Notification]:
        """
        Получить неудачные уведомления для повторной отправки.
        
        Returns:
            Список уведомлений, которые можно отправить повторно
        """
        return [
            n for n in self._notifications.values()
            if (n.status == NotificationStatus.FAILED and 
                n.retry_count < n.max_retries)
        ]
    
    async def update_notification(self, notification_id: str, data: NotificationUpdateData) -> Optional[Notification]:
        """
        Обновить данные уведомления.
        
        Args:
            notification_id: ID уведомления
            data: Данные для обновления
            
        Returns:
            Обновленное уведомление или None
        """
        notification = self._notifications.get(notification_id)
        if not notification:
            return None
        
        # Обновляем поля
        if data.status is not None:
            notification.status = data.status
        if data.sent_at is not None:
            notification.sent_at = data.sent_at
        if data.delivered_at is not None:
            notification.delivered_at = data.delivered_at
        if data.telegram_message_id is not None:
            notification.telegram_message_id = data.telegram_message_id
        if data.retry_count is not None:
            notification.retry_count = data.retry_count
        
        logger.info(f"Уведомление {notification_id} обновлено в памяти")
        return notification
    
    async def delete_notification(self, notification_id: str) -> bool:
        """
        Удалить уведомление.
        
        Args:
            notification_id: ID уведомления для удаления
            
        Returns:
            True если уведомление удалено, False если не найдено
        """
        notification = self._notifications.get(notification_id)
        if not notification:
            return False
        
        # Удаляем из основного хранилища
        del self._notifications[notification_id]
        
        # Удаляем из индекса клиентов
        if notification.client_id in self._client_index:
            if notification_id in self._client_index[notification.client_id]:
                self._client_index[notification.client_id].remove(notification_id)
        
        logger.info(f"Уведомление {notification_id} удалено из памяти")
        return True
    
    async def list_notifications(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[Notification]:
        """
        Получить список всех уведомлений.
        
        Args:
            limit: Максимальное количество уведомлений
            offset: Смещение для пагинации
            
        Returns:
            Список уведомлений
        """
        notifications = list(self._notifications.values())
        
        # Сортируем по дате создания (новые первыми)
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        
        if offset:
            notifications = notifications[offset:]
        if limit:
            notifications = notifications[:limit]
            
        return notifications
    
    async def count_notifications(self) -> int:
        """
        Получить общее количество уведомлений.
        
        Returns:
            Количество уведомлений
        """
        return len(self._notifications)
    
    async def count_notifications_by_client(self, client_id: str) -> int:
        """
        Получить количество уведомлений клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Количество уведомлений клиента
        """
        return len(self._client_index.get(client_id, []))
    
    async def count_notifications_by_status(self, status: NotificationStatus) -> int:
        """
        Получить количество уведомлений по статусу.
        
        Args:
            status: Статус уведомлений
            
        Returns:
            Количество уведомлений с указанным статусом
        """
        return len([n for n in self._notifications.values() if n.status == status])
    
    async def get_notifications_by_priority(self, priority: NotificationPriority) -> List[Notification]:
        """
        Получить уведомления по приоритету.
        
        Args:
            priority: Приоритет уведомлений
            
        Returns:
            Список уведомлений с указанным приоритетом
        """
        return [n for n in self._notifications.values() if n.priority == priority]
    
    async def get_notifications_created_between(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Notification]:
        """
        Получить уведомления, созданные в указанном периоде.
        
        Args:
            start_time: Начало периода
            end_time: Конец периода
            
        Returns:
            Список уведомлений за период
        """
        return [
            n for n in self._notifications.values()
            if start_time <= n.created_at <= end_time
        ]
    
    async def cleanup_old_notifications(self, older_than: datetime) -> int:
        """
        Очистить старые уведомления.
        
        Args:
            older_than: Удалить уведомления старше этой даты
            
        Returns:
            Количество удаленных уведомлений
        """
        old_notifications = [
            n for n in self._notifications.values()
            if n.created_at < older_than
        ]
        
        count = 0
        for notification in old_notifications:
            if await self.delete_notification(notification.id):
                count += 1
        
        logger.info(f"Очищено {count} старых уведомлений из памяти")
        return count
    
    def clear_all(self) -> int:
        """
        Очистить все данные (для тестирования).
        
        Returns:
            Количество удаленных записей
        """
        count = len(self._notifications)
        self._notifications.clear()
        self._client_index.clear()
        
        logger.info(f"Очищено {count} уведомлений из памяти")
        return count 