"""
🕐 Сервис планировщика задач

Управляет автоматическими напоминаниями и фоновыми задачами:
- Напоминания о занятиях
- Обработка просроченных уведомлений  
- Автоматические уведомления после занятий
- Статистические отчеты
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from ..models.client import Client
from ..models.subscription import Subscription
from ..models.notification import Notification, NotificationStatus, NotificationType, NotificationPriority
from ..services.protocols.client_service import ClientServiceProtocol
from ..services.protocols.subscription_service import SubscriptionServiceProtocol
from ..services.protocols.notification_service import NotificationServiceProtocol

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Сервис планировщика задач для автоматических напоминаний.
    
    Управляет:
    - Напоминаниями о занятиях
    - Обработкой просроченных уведомлений
    - Автоматическими уведомлениями
    - Периодическими задачами
    """
    
    def __init__(
        self,
        client_service: ClientServiceProtocol,
        subscription_service: SubscriptionServiceProtocol,
        notification_service: NotificationServiceProtocol
    ):
        """
        Инициализация сервиса планировщика.
        
        Args:
            client_service: Сервис клиентов
            subscription_service: Сервис абонементов
            notification_service: Сервис уведомлений
        """
        self._client_service = client_service
        self._subscription_service = subscription_service
        self._notification_service = notification_service
        
        # Настройка планировщика
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self._scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Europe/Moscow'
        )
        
        self._is_running = False
        logger.info("SchedulerService инициализирован")
    
    async def start(self) -> None:
        """Запуск планировщика и регистрация периодических задач."""
        if self._is_running:
            logger.warning("Планировщик уже запущен")
            return
        
        try:
            # Запускаем планировщик
            self._scheduler.start()
            self._is_running = True
            
            # Регистрируем периодические задачи
            await self._register_periodic_jobs()
            
            logger.info("SchedulerService запущен успешно")
            
        except Exception as e:
            logger.error(f"Ошибка запуска планировщика: {e}")
            raise
    
    async def stop(self) -> None:
        """Остановка планировщика."""
        if not self._is_running:
            return
        
        try:
            self._scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("SchedulerService остановлен")
            
        except Exception as e:
            logger.error(f"Ошибка остановки планировщика: {e}")
    
    async def _register_periodic_jobs(self) -> None:
        """Регистрация периодических задач."""
        
        # Обработка запланированных уведомлений каждые 5 минут
        self._scheduler.add_job(
            self._process_scheduled_notifications,
            trigger=IntervalTrigger(minutes=5),
            id='process_scheduled_notifications',
            name='Обработка запланированных уведомлений',
            replace_existing=True
        )
        
        # Повторная отправка неудачных уведомлений каждые 30 минут
        self._scheduler.add_job(
            self._retry_failed_notifications,
            trigger=IntervalTrigger(minutes=30),
            id='retry_failed_notifications',
            name='Повторная отправка неудачных уведомлений',
            replace_existing=True
        )
        
        # Напоминания о занятиях - каждый день в 18:00
        self._scheduler.add_job(
            self._send_class_reminders,
            trigger=CronTrigger(hour=18, minute=0),
            id='daily_class_reminders',
            name='Ежедневные напоминания о занятиях',
            replace_existing=True
        )
        
        # Проверка истекающих абонементов - каждый день в 10:00
        self._scheduler.add_job(
            self._check_expiring_subscriptions,
            trigger=CronTrigger(hour=10, minute=0),
            id='check_expiring_subscriptions',
            name='Проверка истекающих абонементов',
            replace_existing=True
        )
        
        # Еженедельная статистика - каждый понедельник в 9:00
        self._scheduler.add_job(
            self._send_weekly_stats,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='weekly_stats',
            name='Еженедельная статистика',
            replace_existing=True
        )
        
        # Обработка завершенных занятий - каждые 15 минут
        self._scheduler.add_job(
            self._process_completed_classes,
            trigger=IntervalTrigger(minutes=15),
            id='process_completed_classes',
            name='Обработка завершенных занятий',
            replace_existing=True
        )
        
        logger.info("Периодические задачи зарегистрированы")
    
    async def schedule_class_reminder(
        self,
        client_id: str,
        class_date: datetime,
        class_type: str,
        reminder_hours_before: int = 2
    ) -> str:
        """
        Запланировать напоминание о занятии.
        
        Args:
            client_id: ID клиента
            class_date: Дата и время занятия
            class_type: Тип занятия
            reminder_hours_before: За сколько часов напомнить
            
        Returns:
            ID созданного задания
        """
        # Если дата занятия уже в прошлом – невозможно создать напоминание
        if class_date <= datetime.now():
            logger.warning(f"Дата занятия {class_date} уже прошла – напоминание не планируется")
            return ""

        reminder_time = class_date - timedelta(hours=reminder_hours_before)

        # Если время напоминания уже прошло, переносим его на +1 секунду вперёд
        if reminder_time <= datetime.now():
            reminder_time = datetime.now() + timedelta(seconds=1)
        
        job_id = f"class_reminder_{client_id}_{class_date.strftime('%Y%m%d_%H%M')}"
        
        try:
            self._scheduler.add_job(
                self._send_single_class_reminder,
                trigger=DateTrigger(run_date=reminder_time),
                args=[client_id, class_date, class_type],
                id=job_id,
                name=f"Напоминание о занятии {class_type}",
                replace_existing=True
            )
            
            logger.info(f"Запланировано напоминание для клиента {client_id} на {reminder_time}")
            return job_id
            
        except Exception as e:
            logger.error(f"Ошибка планирования напоминания: {e}")
            return ""
    
    async def schedule_subscription_expiry_reminder(
        self,
        subscription_id: str,
        expiry_date: datetime,
        days_before: int = 3
    ) -> str:
        """
        Запланировать напоминание об истечении абонемента.
        
        Args:
            subscription_id: ID абонемента
            expiry_date: Дата истечения абонемента
            days_before: За сколько дней напомнить
            
        Returns:
            ID созданного задания
        """
        reminder_time = expiry_date - timedelta(days=days_before)
        
        if reminder_time <= datetime.now():
            logger.warning(f"Время напоминания об истечении абонемента уже прошло")
            return ""
        
        job_id = f"subscription_expiry_{subscription_id}_{expiry_date.strftime('%Y%m%d')}"
        
        try:
            self._scheduler.add_job(
                self._send_subscription_expiry_reminder,
                trigger=DateTrigger(run_date=reminder_time),
                args=[subscription_id],
                id=job_id,
                name=f"Напоминание об истечении абонемента",
                replace_existing=True
            )
            
            logger.info(f"Запланировано напоминание об истечении абонемента {subscription_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Ошибка планирования напоминания об истечении: {e}")
            return ""
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Отменить запланированное задание.
        
        Args:
            job_id: ID задания
            
        Returns:
            True если задание отменено успешно
        """
        try:
            self._scheduler.remove_job(job_id)
            logger.info(f"Задание {job_id} отменено")
            return True
            
        except Exception as e:
            logger.warning(f"Не удалось отменить задание {job_id}: {e}")
            return False
    
    async def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """
        Получить список запланированных заданий.
        
        Returns:
            Список заданий с информацией
        """
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            })
        
        return jobs
    
    # Периодические задачи
    
    async def _process_scheduled_notifications(self) -> int:
        """Обработка запланированных уведомлений."""
        try:
            processed_count = await self._notification_service.process_scheduled_notifications()
            if processed_count > 0:
                logger.info(f"Обработано {processed_count} запланированных уведомлений")
            return processed_count
        except Exception as e:
            logger.error(f"Ошибка обработки запланированных уведомлений: {e}")
            return 0
    
    async def _retry_failed_notifications(self) -> None:
        """Повторная отправка неудачных уведомлений."""
        try:
            retried_count = await self._notification_service.retry_failed_notifications()
            if retried_count > 0:
                logger.info(f"Повторно отправлено {retried_count} уведомлений")
                
        except Exception as e:
            logger.error(f"Ошибка повторной отправки уведомлений: {e}")
    
    async def _send_class_reminders(self) -> None:
        """Отправка ежедневных напоминаний о занятиях."""
        try:
            # Получаем всех активных клиентов с активными абонементами
            active_clients = await self._client_service.get_active_clients()
            
            reminder_count = 0
            tomorrow = datetime.now() + timedelta(days=1)
            
            for client in active_clients:
                # Проверяем, есть ли у клиента активные абонементы
                subscriptions = await self._subscription_service.get_client_subscriptions(client.id)
                active_subscriptions = [s for s in subscriptions if s.status.value == 'active']
                
                if active_subscriptions:
                    # Отправляем напоминание о завтрашних занятиях
                    await self._send_daily_schedule_reminder(client.id, tomorrow)
                    reminder_count += 1
            
            logger.info(f"Отправлено {reminder_count} ежедневных напоминаний о занятиях")
            
        except Exception as e:
            logger.error(f"Ошибка отправки ежедневных напоминаний: {e}")
    
    async def _check_expiring_subscriptions(self) -> None:
        """Проверка истекающих абонементов."""
        try:
            # Получаем все активные абонементы
            all_subscriptions = await self._subscription_service.get_all_subscriptions()
            
            # Фильтруем абонементы, истекающие в ближайшие 3 дня
            expiring_soon = []
            check_date = datetime.now().date() + timedelta(days=3)
            
            for subscription in all_subscriptions:
                if (subscription.status.value == 'active' and 
                    subscription.end_date <= check_date):
                    expiring_soon.append(subscription)
            
            # Отправляем уведомления
            for subscription in expiring_soon:
                await self._send_subscription_expiry_reminder(subscription.id)
            
            if expiring_soon:
                logger.info(f"Отправлено {len(expiring_soon)} уведомлений об истекающих абонементах")
                
        except Exception as e:
            logger.error(f"Ошибка проверки истекающих абонементов: {e}")
    
    async def _send_weekly_stats(self) -> None:
        """Отправка еженедельной статистики."""
        try:
            # Здесь будет логика сбора и отправки статистики
            # Пока просто логируем
            logger.info("Отправка еженедельной статистики (заглушка)")
            
        except Exception as e:
            logger.error(f"Ошибка отправки еженедельной статистики: {e}")
    
    # Вспомогательные методы для отправки уведомлений
    
    async def _send_single_class_reminder(
        self,
        client_id: str,
        class_date: datetime,
        class_type: str
    ) -> None:
        """Отправка напоминания о конкретном занятии."""
        try:
            client = await self._client_service.get_client(client_id)
            
            # Создаем уведомление
            notification_data = {
                'client_id': client_id,
                'type': NotificationType.CLASS_REMINDER,
                'title': f'Напоминание о занятии {class_type}',
                'message': f'Привет, {client.name}! 👋\n\n'
                          f'Напоминаем о вашем занятии:\n'
                          f'🧘‍♀️ {class_type}\n'
                          f'🕐 {class_date.strftime("%d.%m.%Y в %H:%M")}\n\n'
                          f'Увидимся на коврике! 🌟',
                'priority': NotificationPriority.HIGH,
                'metadata': {
                    'class_date': class_date.isoformat(),
                    'class_type': class_type
                }
            }
            
            notification_id = await self._notification_service.create_notification(notification_data)
            await self._notification_service.send_notification(notification_id)
            
            logger.info(f"Отправлено напоминание о занятии клиенту {client_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки напоминания о занятии: {e}")
    
    async def _send_subscription_expiry_reminder(self, subscription_id: str) -> None:
        """Отправка напоминания об истечении абонемента."""
        try:
            subscription = await self._subscription_service.get_subscription(subscription_id)
            client = await self._client_service.get_client(subscription.client_id)
            
            remaining_classes = subscription.total_classes - subscription.used_classes
            
            notification_data = {
                'client_id': subscription.client_id,
                'type': NotificationType.SUBSCRIPTION_EXPIRING,
                'title': 'Ваш абонемент скоро истекает',
                'message': f'Привет, {client.name}! 👋\n\n'
                          f'Ваш абонемент истекает {subscription.end_date.strftime("%d.%m.%Y")}\n'
                          f'Осталось занятий: {remaining_classes}\n\n'
                          f'Не забудьте продлить абонемент, чтобы продолжить практику! 🧘‍♀️\n\n'
                          f'Для продления свяжитесь с нами: /contact',
                'priority': NotificationPriority.HIGH,
                'metadata': {
                    'subscription_id': subscription_id,
                    'expiry_date': subscription.end_date.isoformat(),
                    'remaining_classes': remaining_classes
                }
            }
            
            notification_id = await self._notification_service.create_notification(notification_data)
            await self._notification_service.send_notification(notification_id)
            
            logger.info(f"Отправлено напоминание об истечении абонемента {subscription_id}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки напоминания об истечении абонемента: {e}")
    
    async def _send_daily_schedule_reminder(self, client_id: str, date: datetime) -> None:
        """Отправка ежедневного напоминания о расписании."""
        try:
            client = await self._client_service.get_client(client_id)
            
            # Формируем расписание на завтра (упрощенная версия)
            weekday = date.weekday()
            schedule_text = self._get_schedule_for_day(weekday)
            
            notification_data = {
                'client_id': client_id,
                'type': NotificationType.GENERAL_INFO,
                'title': f'Расписание на {date.strftime("%d.%m.%Y")}',
                'message': f'Привет, {client.name}! 👋\n\n'
                          f'Расписание занятий на завтра:\n\n'
                          f'{schedule_text}\n\n'
                          f'Ждем вас на практике! 🧘‍♀️',
                'priority': NotificationPriority.NORMAL,
                'metadata': {
                    'schedule_date': date.isoformat(),
                    'weekday': weekday
                }
            }
            
            notification_id = await self._notification_service.create_notification(notification_data)
            await self._notification_service.send_notification(notification_id)
            
        except Exception as e:
            logger.error(f"Ошибка отправки ежедневного напоминания: {e}")
    
    def _get_schedule_for_day(self, weekday: int) -> str:
        """Получить расписание для дня недели."""
        schedules = {
            0: "🌅 08:00 - Хатха-йога (начинающие)\n🌟 19:00 - Виньяса-флоу (средний)\n🌙 20:45 - Йога-нидра",
            1: "🌅 07:30 - Утренняя практика\n🌟 18:30 - Хатха-йога (средний)\n🌙 20:15 - Инь-йога",
            2: "🌅 08:00 - Аштанга-йога (продвинутый)\n🌟 19:00 - Хатха-йога (начинающие)\n🌙 20:45 - Медитация",
            3: "🌅 07:30 - Виньяса-флоу (средний)\n🌟 18:30 - Хатха-йога (все уровни)\n🌙 20:15 - Восстановительная йога",
            4: "🌅 08:00 - Хатха-йога (начинающие)\n🌟 19:00 - Виньяса-флоу (средний)\n🌙 20:45 - Йога-нидра",
            5: "🌅 09:00 - Утренняя практика\n🌟 11:00 - Семейная йога\n🌙 18:00 - Хатха-йога (все уровни)",
            6: "🌅 10:00 - Медитативная практика\n🌟 12:00 - Инь-йога\n🌙 18:00 - Восстановительная йога"
        }
        
        return schedules.get(weekday, "Расписание уточняется")
    
    async def _process_completed_classes(self) -> None:
        """
        Обработать завершенные занятия для post-class автоматизации.
        
        Эта задача будет интегрирована с PostClassService когда он будет добавлен в main.py
        """
        try:
            logger.info("Обработка завершенных занятий...")
            
            # TODO: Интеграция с PostClassService
            # Пока что просто логируем
            logger.info("Post-class автоматизация будет добавлена в следующем обновлении")
            
        except Exception as e:
            logger.error(f"Ошибка обработки завершенных занятий: {e}") 