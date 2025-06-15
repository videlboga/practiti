"""
📢 Сервис управления уведомлениями Practiti

Бизнес-логика для работы с уведомлениями и напоминаниями клиентов йога-студии.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from ..models.notification import (
    Notification, NotificationCreateData, NotificationUpdateData, 
    NotificationType, NotificationStatus, NotificationPriority,
    NOTIFICATION_TEMPLATES
)
from ..repositories.protocols.notification_repository import NotificationRepositoryProtocol
from ..services.protocols.notification_service import NotificationServiceProtocol
from ..services.protocols.client_service import ClientServiceProtocol
from ..services.protocols.subscription_service import SubscriptionServiceProtocol
from ..utils.exceptions import BusinessLogicError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService(NotificationServiceProtocol):
    """
    Сервис для управления уведомлениями клиентов.
    
    Реализует всю бизнес-логику работы с уведомлениями и напоминаниями.
    """
    
    def __init__(
        self, 
        notification_repository: NotificationRepositoryProtocol,
        client_service: ClientServiceProtocol,
        subscription_service: SubscriptionServiceProtocol
    ):
        """
        Инициализация сервиса.
        
        Args:
            notification_repository: Репозиторий для работы с данными уведомлений
            client_service: Сервис для работы с клиентами
            subscription_service: Сервис для работы с абонементами
        """
        self._repository = notification_repository
        self._client_service = client_service
        self._subscription_service = subscription_service
        
        logger.info("NotificationService инициализирован")
    
    async def create_notification(self, data: NotificationCreateData) -> Notification:
        """
        Создать новое уведомление.
        
        Args:
            data: Данные для создания уведомления
            
        Returns:
            Созданное уведомление
            
        Raises:
            BusinessLogicError: При нарушении бизнес-правил
        """
        logger.info(f"Создание уведомления {data.type.value} для клиента {data.client_id}")
        
        # Проверяем, существует ли клиент
        try:
            await self._client_service.get_client(data.client_id)
        except BusinessLogicError:
            raise BusinessLogicError(f"Клиент с ID {data.client_id} не найден")
        
        # Создаем уведомление через репозиторий
        notification = await self._repository.save_notification(data)
        
        logger.info(f"Уведомление {notification.id} создано успешно")
        return notification
    
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
        # Получаем шаблон
        template = NOTIFICATION_TEMPLATES.get(notification_type)
        if not template:
            raise BusinessLogicError(f"Шаблон для типа {notification_type.value} не найден")
        
        # Форматируем шаблон
        try:
            title, message = template.format_notification(**template_data)
        except ValueError as e:
            raise BusinessLogicError(f"Ошибка форматирования шаблона: {e}")
        
        # Создаем данные уведомления
        notification_data = NotificationCreateData(
            client_id=client_id,
            type=notification_type,
            title=title,
            message=message,
            priority=template.priority,
            scheduled_at=scheduled_at,
            metadata=template_data
        )
        
        return await self.create_notification(notification_data)
    
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
        notification = await self._repository.get_notification_by_id(notification_id)
        if not notification:
            raise BusinessLogicError(f"Уведомление с ID {notification_id} не найдено")
        
        return notification
    
    async def get_all_notifications(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Notification]:
        """
        Получить все уведомления.
        
        Args:
            limit: Максимальное количество уведомлений
            offset: Смещение для пагинации
            
        Returns:
            Список всех уведомлений
        """
        return await self._repository.list_notifications(limit=limit, offset=offset)
    
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
        return await self._repository.get_notifications_by_client_id(client_id, limit=limit)
    
    async def get_pending_notifications(self) -> List[Notification]:
        """
        Получить все ожидающие отправки уведомления.
        
        Returns:
            Список ожидающих уведомлений
        """
        return await self._repository.get_notifications_by_status(NotificationStatus.PENDING)
    
    async def get_scheduled_notifications(self, before_time: datetime) -> List[Notification]:
        """
        Получить запланированные уведомления до указанного времени.
        
        Args:
            before_time: Время, до которого искать уведомления
            
        Returns:
            Список запланированных уведомлений
        """
        return await self._repository.get_scheduled_notifications(before_time)
    
    async def send_notification(self, notification_id: str) -> bool:
        """
        Отправить уведомление.
        
        Args:
            notification_id: ID уведомления
            
        Returns:
            True если отправлено успешно, False иначе
        """
        notification = await self.get_notification(notification_id)
        
        if notification.status != NotificationStatus.PENDING:
            logger.warning(f"Попытка отправить уведомление {notification_id} со статусом {notification.status}")
            return False
        
        # TODO: Здесь будет интеграция с Telegram Bot для отправки
        # Пока просто помечаем как отправленное
        await self.mark_as_sent(notification_id)
        
        logger.info(f"Уведомление {notification_id} отправлено")
        return True
    
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
        try:
            # Создаем уведомление
            notification = await self.create_notification_from_template(
                client_id=client_id,
                notification_type=notification_type,
                template_data=template_data
            )
            
            # Отправляем немедленно
            return await self.send_notification(notification.id)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке немедленного уведомления: {e}")
            return False
    
    async def mark_as_sent(self, notification_id: str, telegram_message_id: Optional[int] = None) -> Notification:
        """
        Отметить уведомление как отправленное.
        
        Args:
            notification_id: ID уведомления
            telegram_message_id: ID сообщения в Telegram
            
        Returns:
            Обновленное уведомление
        """
        update_data = NotificationUpdateData(
            status=NotificationStatus.SENT,
            sent_at=datetime.now(),
            telegram_message_id=telegram_message_id
        )
        
        notification = await self._repository.update_notification(notification_id, update_data)
        if not notification:
            raise BusinessLogicError(f"Уведомление с ID {notification_id} не найдено")
        
        logger.info(f"Уведомление {notification_id} помечено как отправленное")
        return notification
    
    async def mark_as_delivered(self, notification_id: str) -> Notification:
        """
        Отметить уведомление как доставленное.
        
        Args:
            notification_id: ID уведомления
            
        Returns:
            Обновленное уведомление
        """
        update_data = NotificationUpdateData(
            status=NotificationStatus.DELIVERED,
            delivered_at=datetime.now()
        )
        
        notification = await self._repository.update_notification(notification_id, update_data)
        if not notification:
            raise BusinessLogicError(f"Уведомление с ID {notification_id} не найдено")
        
        logger.info(f"Уведомление {notification_id} помечено как доставленное")
        return notification
    
    async def mark_as_failed(self, notification_id: str, error_message: str) -> Notification:
        """
        Отметить уведомление как неудачное.
        
        Args:
            notification_id: ID уведомления
            error_message: Сообщение об ошибке
            
        Returns:
            Обновленное уведомление
        """
        notification = await self.get_notification(notification_id)
        
        update_data = NotificationUpdateData(
            status=NotificationStatus.FAILED,
            retry_count=notification.retry_count + 1
        )
        
        # Добавляем информацию об ошибке в метаданные
        metadata = notification.metadata.copy()
        metadata['last_error'] = error_message
        metadata['failed_at'] = datetime.now().isoformat()
        
        notification = await self._repository.update_notification(notification_id, update_data)
        if not notification:
            raise BusinessLogicError(f"Уведомление с ID {notification_id} не найдено")
        
        logger.error(f"Уведомление {notification_id} помечено как неудачное: {error_message}")
        return notification
    
    async def cancel_notification(self, notification_id: str) -> Notification:
        """
        Отменить уведомление.
        
        Args:
            notification_id: ID уведомления
            
        Returns:
            Обновленное уведомление
        """
        update_data = NotificationUpdateData(
            status=NotificationStatus.CANCELLED
        )
        
        notification = await self._repository.update_notification(notification_id, update_data)
        if not notification:
            raise BusinessLogicError(f"Уведомление с ID {notification_id} не найдено")
        
        logger.info(f"Уведомление {notification_id} отменено")
        return notification
    
    async def retry_failed_notifications(self) -> int:
        """
        Повторить отправку неудачных уведомлений.
        
        Returns:
            Количество уведомлений, отправленных повторно
        """
        failed_notifications = await self._repository.get_failed_notifications_for_retry()
        
        retry_count = 0
        for notification in failed_notifications:
            try:
                # Сбрасываем статус на PENDING для повторной отправки
                update_data = NotificationUpdateData(status=NotificationStatus.PENDING)
                await self._repository.update_notification(notification.id, update_data)
                
                # Пытаемся отправить
                if await self.send_notification(notification.id):
                    retry_count += 1
                    
            except Exception as e:
                logger.error(f"Ошибка при повторной отправке уведомления {notification.id}: {e}")
        
        logger.info(f"Повторно отправлено {retry_count} уведомлений")
        return retry_count
    
    async def process_scheduled_notifications(self) -> int:
        """
        Обработать запланированные уведомления.
        
        Отправляет все уведомления, время которых наступило.
        
        Returns:
            Количество обработанных уведомлений
        """
        current_time = datetime.now()
        scheduled_notifications = await self.get_scheduled_notifications(current_time)
        
        processed_count = 0
        for notification in scheduled_notifications:
            try:
                if await self.send_notification(notification.id):
                    processed_count += 1
            except Exception as e:
                logger.error(f"Ошибка при обработке запланированного уведомления {notification.id}: {e}")
        
        logger.info(f"Обработано {processed_count} запланированных уведомлений")
        return processed_count
    
    async def send_subscription_expiring_notifications(self, days_before: int = 3) -> int:
        """
        Отправить уведомления об истекающих абонементах.
        
        Args:
            days_before: За сколько дней до истечения отправлять
            
        Returns:
            Количество отправленных уведомлений
        """
        logger.info(f"Поиск абонементов, истекающих через {days_before} дней")
        
        # Получаем все активные абонементы
        # TODO: Добавить метод в SubscriptionService для получения истекающих абонементов
        # Пока используем заглушку
        
        sent_count = 0
        # expiring_subscriptions = await self._subscription_service.get_expiring_subscriptions(days_before)
        
        # for subscription in expiring_subscriptions:
        #     try:
        #         client = await self._client_service.get_client(subscription.client_id)
        #         
        #         template_data = {
        #             'client_name': client.name,
        #             'subscription_type': subscription.type.value,
        #             'end_date': subscription.end_date.strftime('%d.%m.%Y'),
        #             'remaining_classes': subscription.remaining_classes
        #         }
        #         
        #         if await self.send_immediate_notification(
        #             client_id=subscription.client_id,
        #             notification_type=NotificationType.SUBSCRIPTION_EXPIRING,
        #             template_data=template_data
        #         ):
        #             sent_count += 1
        #             
        #     except Exception as e:
        #         logger.error(f"Ошибка при отправке уведомления об истекающем абонементе {subscription.id}: {e}")
        
        logger.info(f"Отправлено {sent_count} уведомлений об истекающих абонементах")
        return sent_count
    
    async def send_classes_running_out_notifications(self, classes_threshold: int = 2) -> int:
        """
        Отправить уведомления о заканчивающихся занятиях.
        
        Args:
            classes_threshold: При каком количестве занятий отправлять
            
        Returns:
            Количество отправленных уведомлений
        """
        logger.info(f"Поиск абонементов с {classes_threshold} или менее занятиями")
        
        sent_count = 0
        # TODO: Добавить метод в SubscriptionService для получения абонементов с малым количеством занятий
        # low_classes_subscriptions = await self._subscription_service.get_subscriptions_with_low_classes(classes_threshold)
        
        # for subscription in low_classes_subscriptions:
        #     try:
        #         client = await self._client_service.get_client(subscription.client_id)
        #         
        #         template_data = {
        #             'client_name': client.name,
        #             'remaining_classes': subscription.remaining_classes
        #         }
        #         
        #         if await self.send_immediate_notification(
        #             client_id=subscription.client_id,
        #             notification_type=NotificationType.CLASSES_RUNNING_OUT,
        #             template_data=template_data
        #         ):
        #             sent_count += 1
        #             
        #     except Exception as e:
        #         logger.error(f"Ошибка при отправке уведомления о заканчивающихся занятиях {subscription.id}: {e}")
        
        logger.info(f"Отправлено {sent_count} уведомлений о заканчивающихся занятиях")
        return sent_count
    
    async def get_notification_statistics(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить статистику по уведомлениям.
        
        Args:
            client_id: ID клиента (если None, то общая статистика)
            
        Returns:
            Словарь со статистикой
        """
        if client_id:
            # Статистика по конкретному клиенту
            notifications = await self.get_client_notifications(client_id)
            
            stats = {
                'client_id': client_id,
                'total_notifications': len(notifications),
                'by_status': {},
                'by_type': {},
                'by_priority': {},
                'recent_notifications': []
            }
            
            # Группируем по статусам
            for notification in notifications:
                status = notification.status.value
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Группируем по типам
                ntype = notification.type.value
                stats['by_type'][ntype] = stats['by_type'].get(ntype, 0) + 1
                
                # Группируем по приоритетам
                priority = notification.priority.value
                stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            
            # Последние 5 уведомлений
            stats['recent_notifications'] = [
                {
                    'id': n.id,
                    'type': n.type.value,
                    'title': n.title,
                    'status': n.status.value,
                    'created_at': n.created_at.isoformat()
                }
                for n in notifications[:5]
            ]
            
        else:
            # Общая статистика
            total_count = await self._repository.count_notifications()
            
            stats = {
                'total_notifications': total_count,
                'by_status': {},
                'by_type': {},
                'by_priority': {},
                'system_health': {}
            }
            
            # Статистика по статусам
            for status in NotificationStatus:
                count = await self._repository.count_notifications_by_status(status)
                if count > 0:
                    stats['by_status'][status.value] = count
            
            # Статистика по типам
            for ntype in NotificationType:
                notifications = await self._repository.get_notifications_by_type(ntype)
                if notifications:
                    stats['by_type'][ntype.value] = len(notifications)
            
            # Статистика по приоритетам
            for priority in NotificationPriority:
                notifications = await self._repository.get_notifications_by_priority(priority)
                if notifications:
                    stats['by_priority'][priority.value] = len(notifications)
            
            # Здоровье системы
            pending_count = stats['by_status'].get('pending', 0)
            failed_count = stats['by_status'].get('failed', 0)
            
            stats['system_health'] = {
                'pending_notifications': pending_count,
                'failed_notifications': failed_count,
                'needs_attention': failed_count > 0 or pending_count > 10
            }
        
        return stats
    
    # Утилитарные методы для интеграции с другими сервисами
    
    async def send_welcome_notification(self, client_id: str, client_name: str) -> bool:
        """
        Отправить приветственное уведомление новому клиенту.
        
        Args:
            client_id: ID клиента
            client_name: Имя клиента
            
        Returns:
            True если отправлено успешно
        """
        template_data = {'client_name': client_name}
        
        return await self.send_immediate_notification(
            client_id=client_id,
            notification_type=NotificationType.WELCOME_MESSAGE,
            template_data=template_data
        )
    
    async def send_registration_complete_notification(self, client_id: str, client_name: str) -> bool:
        """
        Отправить уведомление о завершении регистрации.
        
        Args:
            client_id: ID клиента
            client_name: Имя клиента
            
        Returns:
            True если отправлено успешно
        """
        template_data = {'client_name': client_name}
        
        return await self.send_immediate_notification(
            client_id=client_id,
            notification_type=NotificationType.REGISTRATION_COMPLETE,
            template_data=template_data
        )
    
    async def send_subscription_purchased_notification(
        self, 
        client_id: str, 
        client_name: str,
        subscription_type: str,
        total_classes: int,
        end_date: str,
        price: int
    ) -> bool:
        """
        Отправить уведомление о покупке абонемента.
        
        Args:
            client_id: ID клиента
            client_name: Имя клиента
            subscription_type: Тип абонемента
            total_classes: Общее количество занятий
            end_date: Дата окончания абонемента
            price: Стоимость абонемента
            
        Returns:
            True если отправлено успешно
        """
        template_data = {
            'client_name': client_name,
            'subscription_type': subscription_type,
            'total_classes': total_classes,
            'end_date': end_date,
            'price': price
        }
        
        return await self.send_immediate_notification(
            client_id=client_id,
            notification_type=NotificationType.SUBSCRIPTION_PURCHASED,
            template_data=template_data
        )
    
    async def send_general_info_notification(
        self, 
        client_id: str, 
        client_name: str, 
        message: str
    ) -> bool:
        """
        Отправить общее информационное уведомление.
        
        Args:
            client_id: ID клиента
            client_name: Имя клиента
            message: Текст сообщения
            
        Returns:
            True если отправлено успешно
        """
        template_data = {
            'client_name': client_name,
            'message': message
        }
        
        return await self.send_immediate_notification(
            client_id=client_id,
            notification_type=NotificationType.GENERAL_INFO,
            template_data=template_data
        ) 