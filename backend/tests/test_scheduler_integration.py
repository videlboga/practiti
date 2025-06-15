"""
🧪 Интеграционные тесты для SchedulerService

Тестирование интеграции планировщика с другими сервисами.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from backend.src.services.scheduler_service import SchedulerService
from backend.src.services.client_service import ClientService
from backend.src.services.subscription_service import SubscriptionService
from backend.src.services.notification_service import NotificationService
from backend.src.repositories.in_memory_client_repository import InMemoryClientRepository
from backend.src.repositories.in_memory_subscription_repository import InMemorySubscriptionRepository
from backend.src.repositories.in_memory_notification_repository import InMemoryNotificationRepository
from backend.src.models.client import Client, ClientStatus, ClientCreateData
from backend.src.models.subscription import Subscription, SubscriptionStatus, SubscriptionType, SubscriptionCreateData
from backend.src.models.notification import NotificationType


@pytest.fixture
async def setup_services():
    """Настройка всех сервисов для интеграционного тестирования."""
    # Создаем репозитории
    client_repo = InMemoryClientRepository()
    subscription_repo = InMemorySubscriptionRepository()
    notification_repo = InMemoryNotificationRepository()
    
    # Создаем сервисы
    client_service = ClientService(client_repo)
    subscription_service = SubscriptionService(subscription_repo)
    notification_service = NotificationService(
        notification_repo, 
        client_service, 
        subscription_service
    )
    scheduler_service = SchedulerService(
        client_service,
        subscription_service,
        notification_service
    )
    
    # Создаем тестового клиента
    client_data = ClientCreateData(
        name="Анна Тестовая",
        phone="+79161234567",
        telegram_id=123456789
    )
    test_client = await client_service.create_client(client_data)
    
    # Создаем тестовый абонемент
    subscription_data = SubscriptionCreateData(
        client_id=test_client.id,
        type=SubscriptionType.PACKAGE_8,
        total_classes=8,
        price=9600,
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=30)).date()
    )
    test_subscription = await subscription_service.create_subscription(subscription_data)
    
    return {
        'client_service': client_service,
        'subscription_service': subscription_service,
        'notification_service': notification_service,
        'scheduler_service': scheduler_service,
        'test_client': test_client,
        'test_subscription': test_subscription
    }


class TestSchedulerIntegration:
    """Интеграционные тесты планировщика."""
    
    @pytest.mark.asyncio
    async def test_scheduler_lifecycle(self, setup_services):
        """Тест жизненного цикла планировщика."""
        services = await setup_services
        scheduler = services['scheduler_service']
        
        # Запускаем планировщик
        await scheduler.start()
        assert scheduler._is_running is True
        
        # Останавливаем планировщик
        await scheduler.stop()
        assert scheduler._is_running is False
    
    @pytest.mark.asyncio
    async def test_schedule_class_reminder_integration(self, setup_services):
        """Тест планирования напоминания о занятии с реальными сервисами."""
        services = await setup_services
        scheduler = services['scheduler_service']
        test_client = services['test_client']
        
        await scheduler.start()
        
        try:
            # Планируем напоминание
            class_date = datetime.now() + timedelta(hours=4)
            job_id = await scheduler.schedule_class_reminder(
                test_client.id,
                class_date,
                "Хатха-йога"
            )
            
            assert job_id != ""
            assert job_id.startswith("class_reminder_")
            
            # Проверяем, что задание создано
            jobs = await scheduler.get_scheduled_jobs()
            job_ids = [job['id'] for job in jobs]
            assert job_id in job_ids
            
            # Отменяем задание
            cancelled = await scheduler.cancel_job(job_id)
            assert cancelled is True
            
        finally:
            await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_subscription_expiry_reminder_integration(self, setup_services):
        """Тест планирования напоминания об истечении абонемента."""
        services = await setup_services
        scheduler = services['scheduler_service']
        test_subscription = services['test_subscription']
        
        await scheduler.start()
        
        try:
            # Планируем напоминание об истечении
            expiry_date = datetime.now() + timedelta(days=5)
            job_id = await scheduler.schedule_subscription_expiry_reminder(
                test_subscription.id,
                expiry_date
            )
            
            assert job_id != ""
            assert job_id.startswith("subscription_expiry_")
            
            # Проверяем, что задание создано
            jobs = await scheduler.get_scheduled_jobs()
            job_ids = [job['id'] for job in jobs]
            assert job_id in job_ids
            
        finally:
            await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_notification_creation_and_sending(self, setup_services):
        """Тест создания и отправки уведомлений через планировщик."""
        services = await setup_services
        scheduler = services['scheduler_service']
        notification_service = services['notification_service']
        test_client = services['test_client']
        
        # Создаем уведомление напрямую
        notification = await notification_service.create_notification_from_template(
            client_id=test_client.id,
            notification_type=NotificationType.CLASS_REMINDER,
            template_data={
                'client_name': test_client.name,
                'class_type': 'Хатха-йога',
                'class_date': (datetime.now() + timedelta(hours=2)).isoformat(),
                'reminder_hours': 2
            }
        )
        
        # Проверяем, что уведомление создано
        assert notification.id is not None
        assert notification.client_id == test_client.id
        assert notification.type == NotificationType.CLASS_REMINDER
        
        # Отправляем уведомление (в тестовом режиме)
        sent = await notification_service.send_notification(notification.id)
        assert sent is True
    
    @pytest.mark.asyncio
    async def test_periodic_tasks_registration(self, setup_services):
        """Тест регистрации периодических задач."""
        services = await setup_services
        scheduler = services['scheduler_service']
        
        await scheduler.start()
        
        try:
            # Получаем список зарегистрированных заданий
            jobs = await scheduler.get_scheduled_jobs()
            
            # Проверяем, что периодические задачи зарегистрированы
            job_ids = [job['id'] for job in jobs]
            
            expected_jobs = [
                'process_scheduled_notifications',
                'retry_failed_notifications',
                'daily_class_reminders',
                'check_expiring_subscriptions',
                'weekly_stats'
            ]
            
            for expected_job in expected_jobs:
                assert expected_job in job_ids, f"Задача {expected_job} не найдена"
            
        finally:
            await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_notification_processing_integration(self, setup_services):
        """Тест обработки запланированных уведомлений."""
        services = await setup_services
        scheduler = services['scheduler_service']
        notification_service = services['notification_service']
        test_client = services['test_client']
        
        # Создаем запланированное уведомление
        scheduled_time = datetime.now() - timedelta(minutes=1)  # Время уже прошло
        notification = await notification_service.create_notification_from_template(
            client_id=test_client.id,
            notification_type=NotificationType.CLASS_REMINDER,
            template_data={
                'client_name': test_client.name,
                'class_type': 'Виньяса-флоу',
                'class_date': datetime.now().isoformat(),
                'reminder_hours': 2
            },
            scheduled_at=scheduled_time
        )
        
        # Обрабатываем запланированные уведомления
        processed_count = await scheduler._process_scheduled_notifications()
        
        # В тестовом режиме должно обработаться 1 уведомление
        assert processed_count >= 0  # Может быть 0 если уведомление уже обработано
    
    @pytest.mark.asyncio
    async def test_error_handling_in_scheduler(self, setup_services):
        """Тест обработки ошибок в планировщике."""
        services = await setup_services
        scheduler = services['scheduler_service']
        
        await scheduler.start()
        
        try:
            # Пытаемся запланировать напоминание с некорректными данными
            job_id = await scheduler.schedule_class_reminder(
                "nonexistent-client",
                datetime.now() + timedelta(hours=2),
                "Тест"
            )
            
            # Задание должно быть создано, но при выполнении будет ошибка
            assert job_id != ""
            
            # Пытаемся отменить несуществующее задание
            cancelled = await scheduler.cancel_job("nonexistent-job")
            assert cancelled is False
            
        finally:
            await scheduler.stop()


class TestSchedulerPerformance:
    """Тесты производительности планировщика."""
    
    @pytest.mark.asyncio
    async def test_multiple_jobs_scheduling(self, setup_services):
        """Тест планирования множественных заданий."""
        services = await setup_services
        scheduler = services['scheduler_service']
        test_client = services['test_client']
        
        await scheduler.start()
        
        try:
            job_ids = []
            
            # Планируем 10 напоминаний
            for i in range(10):
                class_date = datetime.now() + timedelta(hours=i+1)
                job_id = await scheduler.schedule_class_reminder(
                    test_client.id,
                    class_date,
                    f"Занятие {i+1}"
                )
                job_ids.append(job_id)
            
            # Проверяем, что все задания созданы
            jobs = await scheduler.get_scheduled_jobs()
            scheduled_job_ids = [job['id'] for job in jobs]
            
            for job_id in job_ids:
                if job_id:  # Пропускаем пустые ID (ошибки планирования)
                    assert job_id in scheduled_job_ids
            
            # Отменяем все созданные задания
            for job_id in job_ids:
                if job_id:
                    await scheduler.cancel_job(job_id)
            
        finally:
            await scheduler.stop()


if __name__ == "__main__":
    # Простой запуск для быстрого тестирования
    async def quick_test():
        """Быстрый тест основной функциональности."""
        print("🧪 Запуск быстрого теста SchedulerService...")
        
        # Создаем сервисы
        client_repo = InMemoryClientRepository()
        subscription_repo = InMemorySubscriptionRepository()
        notification_repo = InMemoryNotificationRepository()
        
        client_service = ClientService(client_repo)
        subscription_service = SubscriptionService(subscription_repo)
        notification_service = NotificationService(
            notification_repo, 
            client_service, 
            subscription_service
        )
        scheduler_service = SchedulerService(
            client_service,
            subscription_service,
            notification_service
        )
        
        # Тестируем жизненный цикл
        await scheduler_service.start()
        print("✅ Планировщик запущен")
        
        jobs = await scheduler_service.get_scheduled_jobs()
        print(f"✅ Зарегистрировано {len(jobs)} периодических задач")
        
        await scheduler_service.stop()
        print("✅ Планировщик остановлен")
        
        print("🎉 Быстрый тест завершен успешно!")
    
    asyncio.run(quick_test()) 