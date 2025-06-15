"""
📢 Протокол сервиса уведомлений Practiti

Интерфейс для работы с уведомлениями и напоминаниями клиентов йога-студии.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from ...models.notification import (
    Notification, NotificationCreateData, NotificationUpdateData, 
    NotificationType, NotificationStatus, NotificationPriority
)


class NotificationServiceProtocol(ABC):
    """
    Протокол сервиса для работы с уведомлениями.
    
    Определяет интерфейс для всех операций с уведомлениями клиентов.
    """
    
    @abstractmethod
    async def create_notification(self, data: NotificationCreateData) -> Notification:
        """
        Создать новое уведомление.
        
        Args:
            data: Данные для создания уведомления
            
        Returns:
            Созданное уведомление
            
        Raises:
            ValidationError: При некорректных данных
            BusinessLogicError: При нарушении бизнес-правил
        """
        pass
    
    @abstractmethod
    async def create_notification_from_template(
        self, 
        client_id: str, 
        notification_type: NotificationType, 
        template_data: Dict[str, Any],
        scheduled_at: Optional[datetime] = None
    ) -> Notification:
        """
        Создать уведомление из шаблона.
        
        Args:
            client_id: ID клиента-получателя
            notification_type: Тип уведомления
            template_data: Данные для подстановки в шаблон
            scheduled_at: Запланированное время отправки
            
        Returns:
            Созданное уведомление
        """
        pass
    
    @abstractmethod
    async def send_notification(self, notification_id: str) -> bool:
        """
        Отправить уведомление.
        
        Args:
            notification_id: ID уведомления
            
        Returns:
            True если отправлено успешно, False иначе
        """
        pass
    
    @abstractmethod
    async def send_immediate_notification(
        self, 
        client_id: str, 
        notification_type: NotificationType, 
        template_data: Dict[str, Any]
    ) -> bool:
        """
        Создать и немедленно отправить уведомление.
        
        Args:
            client_id: ID клиента-получателя
            notification_type: Тип уведомления
            template_data: Данные для подстановки в шаблон
            
        Returns:
            True если отправлено успешно, False иначе
        """
        pass
    
    @abstractmethod
    async def get_notification(self, notification_id: str) -> Notification:
        """
        Получить уведомление по ID.
        
        Args:
            notification_id: ID уведомления
            
        Returns:
            Уведомление
            
        Raises:
            BusinessLogicError: Если уведомление не найдено
        """
        pass
    
    @abstractmethod
    async def get_all_notifications(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Notification]:
        """
        Получить все уведомления.
        
        Args:
            limit: Максимальное количество уведомлений
            offset: Смещение для пагинации
            
        Returns:
            Список всех уведомлений
        """
        pass
    
    @abstractmethod
    async def get_client_notifications(
        self, 
        client_id: str, 
        limit: Optional[int] = None
    ) -> List[Notification]:
        """
        Получить уведомления клиента.
        
        Args:
            client_id: ID клиента
            limit: Максимальное количество уведомлений
            
        Returns:
            Список уведомлений клиента
        """
        pass
    
    @abstractmethod
    async def get_pending_notifications(self) -> List[Notification]:
        """
        Получить все ожидающие отправки уведомления.
        
        Returns:
            Список ожидающих уведомлений
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
    async def mark_as_sent(self, notification_id: str, telegram_message_id: Optional[int] = None) -> Notification:
        """
        Отметить уведомление как отправленное.
        
        Args:
            notification_id: ID уведомления
            telegram_message_id: ID сообщения в Telegram
            
        Returns:
            Обновленное уведомление
        """
        pass
    
    @abstractmethod
    async def mark_as_delivered(self, notification_id: str) -> Notification:
        """
        Отметить уведомление как доставленное.
        
        Args:
            notification_id: ID уведомления
            
        Returns:
            Обновленное уведомление
        """
        pass
    
    @abstractmethod
    async def mark_as_failed(self, notification_id: str, error_message: str) -> Notification:
        """
        Отметить уведомление как неудачное.
        
        Args:
            notification_id: ID уведомления
            error_message: Сообщение об ошибке
            
        Returns:
            Обновленное уведомление
        """
        pass
    
    @abstractmethod
    async def retry_failed_notifications(self) -> int:
        """
        Повторить отправку неудачных уведомлений.
        
        Returns:
            Количество уведомлений, отправленных повторно
        """
        pass
    
    @abstractmethod
    async def cancel_notification(self, notification_id: str) -> Notification:
        """
        Отменить уведомление.
        
        Args:
            notification_id: ID уведомления
            
        Returns:
            Обновленное уведомление
        """
        pass
    
    @abstractmethod
    async def process_scheduled_notifications(self) -> int:
        """
        Обработать запланированные уведомления.
        
        Отправляет все уведомления, время которых наступило.
        
        Returns:
            Количество обработанных уведомлений
        """
        pass
    
    @abstractmethod
    async def send_subscription_expiring_notifications(self, days_before: int = 3) -> int:
        """
        Отправить уведомления об истекающих абонементах.
        
        Args:
            days_before: За сколько дней до истечения отправлять
            
        Returns:
            Количество отправленных уведомлений
        """
        pass
    
    @abstractmethod
    async def send_classes_running_out_notifications(self, classes_threshold: int = 2) -> int:
        """
        Отправить уведомления о заканчивающихся занятиях.
        
        Args:
            classes_threshold: При каком количестве занятий отправлять
            
        Returns:
            Количество отправленных уведомлений
        """
        pass
    
    @abstractmethod
    async def get_notification_statistics(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить статистику по уведомлениям.
        
        Args:
            client_id: ID клиента (если None, то общая статистика)
            
        Returns:
            Словарь со статистикой
        """
        pass 