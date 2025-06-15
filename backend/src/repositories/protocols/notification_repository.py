"""
📢 Протокол репозитория уведомлений Practiti

Интерфейс для работы с данными уведомлений в любом хранилище.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ...models.notification import (
    Notification, NotificationCreateData, NotificationUpdateData, 
    NotificationStatus, NotificationType, NotificationPriority
)


class NotificationRepositoryProtocol(ABC):
    """
    Протокол репозитория для работы с уведомлениями.
    
    Определяет интерфейс для всех операций с данными уведомлений.
    """
    
    @abstractmethod
    async def save_notification(self, data: NotificationCreateData) -> Notification:
        """
        Сохранить новое уведомление.
        
        Args:
            data: Данные для создания уведомления
            
        Returns:
            Созданное уведомление с присвоенным ID
        """
        pass
    
    @abstractmethod
    async def get_notification_by_id(self, notification_id: str) -> Optional[Notification]:
        """
        Получить уведомление по ID.
        
        Args:
            notification_id: Уникальный ID уведомления
            
        Returns:
            Уведомление или None если не найдено
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_notifications_by_status(self, status: NotificationStatus) -> List[Notification]:
        """
        Получить уведомления по статусу.
        
        Args:
            status: Статус уведомлений
            
        Returns:
            Список уведомлений с указанным статусом
        """
        pass
    
    @abstractmethod
    async def get_notifications_by_type(self, notification_type: NotificationType) -> List[Notification]:
        """
        Получить уведомления по типу.
        
        Args:
            notification_type: Тип уведомлений
            
        Returns:
            Список уведомлений указанного типа
        """
        pass
    
    @abstractmethod
    async def get_scheduled_notifications(self, before_time: datetime) -> List[Notification]:
        """
        Получить запланированные уведомления до указанного времени.
        
        Args:
            before_time: Время, до которого искать уведомления
            
        Returns:
            Список запланированных уведомлений
        """
        pass
    
    @abstractmethod
    async def get_failed_notifications_for_retry(self) -> List[Notification]:
        """
        Получить неудачные уведомления для повторной отправки.
        
        Returns:
            Список уведомлений, которые можно отправить повторно
        """
        pass
    
    @abstractmethod
    async def update_notification(self, notification_id: str, data: NotificationUpdateData) -> Optional[Notification]:
        """
        Обновить данные уведомления.
        
        Args:
            notification_id: ID уведомления для обновления
            data: Новые данные уведомления
            
        Returns:
            Обновлённое уведомление или None если не найдено
        """
        pass
    
    @abstractmethod
    async def delete_notification(self, notification_id: str) -> bool:
        """
        Удалить уведомление.
        
        Args:
            notification_id: ID уведомления для удаления
            
        Returns:
            True если уведомление удалено, False если не найдено
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def count_notifications(self) -> int:
        """
        Получить общее количество уведомлений.
        
        Returns:
            Количество уведомлений
        """
        pass
    
    @abstractmethod
    async def count_notifications_by_client(self, client_id: str) -> int:
        """
        Получить количество уведомлений клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Количество уведомлений клиента
        """
        pass
    
    @abstractmethod
    async def count_notifications_by_status(self, status: NotificationStatus) -> int:
        """
        Получить количество уведомлений по статусу.
        
        Args:
            status: Статус уведомлений
            
        Returns:
            Количество уведомлений с указанным статусом
        """
        pass
    
    @abstractmethod
    async def get_notifications_by_priority(self, priority: NotificationPriority) -> List[Notification]:
        """
        Получить уведомления по приоритету.
        
        Args:
            priority: Приоритет уведомлений
            
        Returns:
            Список уведомлений с указанным приоритетом
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def cleanup_old_notifications(self, older_than: datetime) -> int:
        """
        Очистить старые уведомления.
        
        Args:
            older_than: Удалить уведомления старше этой даты
            
        Returns:
            Количество удаленных уведомлений
        """
        pass 