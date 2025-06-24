"""
🧪 Тесты для SchedulerService

Тестирование функциональности планировщика задач:
- Запуск и остановка планировщика
- Планирование напоминаний
- Периодические задачи
- Управление заданиями
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from backend.src.services.scheduler_service import SchedulerService
from backend.src.models.client import Client, ClientStatus
from backend.src.models.subscription import Subscription, SubscriptionStatus, SubscriptionType
from backend.src.models.notification import Notification, NotificationStatus, NotificationType, NotificationPriority


@pytest.fixture
def mock_client_service():
    """Мок сервиса клиентов."""
    service = AsyncMock()
    
    # Настраиваем возвращаемые значения
    sample_client = Client(
        id="test-client-1",
        name="Анна Петрова",
        phone="+79161234567",
        telegram_id=123456789,
        yoga_experience=True,
        intensity_preference="средняя",
        time_preference="утро",
        status=ClientStatus.ACTIVE
    )
    
    service.get_client.return_value = sample_client
    service.get_active_clients.return_value = [sample_client]
    
    return service


@pytest.fixture
def mock_subscription_service():
    """Мок сервиса абонементов."""
    service = AsyncMock()
    
    # Настраиваем возвращаемые значения
    sample_subscription = Subscription(
        id="test-subscription-1",
        client_id="test-client-1",
        type=SubscriptionType.PACKAGE_8,
        total_classes=8,
        used_classes=2,
        price=9600,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=30)).date(),
        created_at=datetime.now()
    )
    
    service.get_subscription.return_value = sample_subscription
    service.get_client_subscriptions.return_value = [sample_subscription]
    service.get_all_subscriptions.return_value = [sample_subscription]
    
    return service


@pytest.fixture
def mock_notification_service():
    """Мок сервиса уведомлений."""
    service = AsyncMock()
    
    service.create_notification.return_value = "test-notification-1"
    service.send_notification.return_value = True
    service.process_scheduled_notifications.return_value = 5
    service.retry_failed_notifications.return_value = 2
    
    return service


@pytest.fixture
def scheduler_service(mock_client_service, mock_subscription_service, mock_notification_service):
    """Экземпляр SchedulerService для тестов."""
    return SchedulerService(
        mock_client_service,
        mock_subscription_service,
        mock_notification_service
    )


class TestSchedulerServiceInitialization:
    """Тесты инициализации SchedulerService."""
    
    def test_scheduler_service_initialization(self, scheduler_service):
        """Тест успешной инициализации сервиса."""
        assert scheduler_service._client_service is not None
        assert scheduler_service._subscription_service is not None
        assert scheduler_service._notification_service is not None
        assert scheduler_service._scheduler is not None
        assert scheduler_service._is_running is False
    
    def test_scheduler_configuration(self, scheduler_service):
        """Тест конфигурации планировщика."""
        scheduler = scheduler_service._scheduler
        
        # Проверяем настройки планировщика
        assert scheduler.timezone.zone == 'Europe/Moscow'
        assert 'default' in scheduler._jobstores
        assert 'default' in scheduler._executors


class TestSchedulerLifecycle:
    """Тесты жизненного цикла планировщика."""
    
    @pytest.mark.asyncio
    async def test_start_scheduler_success(self, scheduler_service):
        """Тест успешного запуска планировщика."""
        with patch.object(scheduler_service._scheduler, 'start') as mock_start:
            await scheduler_service.start()
            
            assert scheduler_service._is_running is True
            mock_start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_scheduler_already_running(self, scheduler_service):
        """Тест попытки запуска уже работающего планировщика."""
        scheduler_service._is_running = True
        
        with patch.object(scheduler_service._scheduler, 'start') as mock_start:
            await scheduler_service.start()
            
            # Планировщик не должен запускаться повторно
            mock_start.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_stop_scheduler_success(self, scheduler_service):
        """Тест успешной остановки планировщика."""
        scheduler_service._is_running = True
        
        with patch.object(scheduler_service._scheduler, 'shutdown') as mock_shutdown:
            await scheduler_service.stop()
            
            assert scheduler_service._is_running is False
            mock_shutdown.assert_called_once_with(wait=True)
    
    @pytest.mark.asyncio
    async def test_stop_scheduler_not_running(self, scheduler_service):
        """Тест остановки неработающего планировщика."""
        scheduler_service._is_running = False
        
        with patch.object(scheduler_service._scheduler, 'shutdown') as mock_shutdown:
            await scheduler_service.stop()
            
            # Остановка не должна вызываться
            mock_shutdown.assert_not_called()


class TestJobScheduling:
    """Тесты планирования заданий."""
    
    @pytest.mark.asyncio
    async def test_schedule_class_reminder_success(self, scheduler_service):
        """Тест успешного планирования напоминания о занятии."""
        client_id = "test-client-1"
        class_date = datetime.now() + timedelta(hours=4)
        class_type = "Хатха-йога"
        
        with patch.object(scheduler_service._scheduler, 'add_job') as mock_add_job:
            job_id = await scheduler_service.schedule_class_reminder(
                client_id, class_date, class_type
            )
            
            assert job_id != ""
            assert job_id.startswith("class_reminder_")
            mock_add_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schedule_class_reminder_past_time(self, scheduler_service):
        """Тест планирования напоминания на прошедшее время."""
        client_id = "test-client-1"
        class_date = datetime.now() - timedelta(hours=1)  # Прошедшее время
        class_type = "Хатха-йога"
        
        with patch.object(scheduler_service._scheduler, 'add_job') as mock_add_job:
            job_id = await scheduler_service.schedule_class_reminder(
                client_id, class_date, class_type
            )
            
            assert job_id == ""  # Пустой ID при ошибке
            mock_add_job.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_schedule_subscription_expiry_reminder_success(self, scheduler_service):
        """Тест успешного планирования напоминания об истечении абонемента."""
        subscription_id = "test-subscription-1"
        expiry_date = datetime.now() + timedelta(days=5)
        
        with patch.object(scheduler_service._scheduler, 'add_job') as mock_add_job:
            job_id = await scheduler_service.schedule_subscription_expiry_reminder(
                subscription_id, expiry_date
            )
            
            assert job_id != ""
            assert job_id.startswith("subscription_expiry_")
            mock_add_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_job_success(self, scheduler_service):
        """Тест успешной отмены задания."""
        job_id = "test-job-1"
        
        with patch.object(scheduler_service._scheduler, 'remove_job') as mock_remove_job:
            result = await scheduler_service.cancel_job(job_id)
            
            assert result is True
            mock_remove_job.assert_called_once_with(job_id)
    
    @pytest.mark.asyncio
    async def test_cancel_job_not_found(self, scheduler_service):
        """Тест отмены несуществующего задания."""
        job_id = "nonexistent-job"
        
        with patch.object(scheduler_service._scheduler, 'remove_job', side_effect=Exception("Job not found")):
            result = await scheduler_service.cancel_job(job_id)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_scheduled_jobs(self, scheduler_service):
        """Тест получения списка запланированных заданий."""
        # Мокаем задания
        mock_job = MagicMock()
        mock_job.id = "test-job-1"
        mock_job.name = "Test Job"
        mock_job.next_run_time = datetime.now()
        mock_job.trigger = "interval"
        
        with patch.object(scheduler_service._scheduler, 'get_jobs', return_value=[mock_job]):
            jobs = await scheduler_service.get_scheduled_jobs()
            
            assert len(jobs) == 1
            assert jobs[0]['id'] == "test-job-1"
            assert jobs[0]['name'] == "Test Job"


class TestPeriodicTasks:
    """Тесты периодических задач."""
    
    @pytest.mark.asyncio
    async def test_process_scheduled_notifications(self, scheduler_service, mock_notification_service):
        """Тест обработки запланированных уведомлений."""
        await scheduler_service._process_scheduled_notifications()
        
        mock_notification_service.process_scheduled_notifications.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retry_failed_notifications(self, scheduler_service, mock_notification_service):
        """Тест повторной отправки неудачных уведомлений."""
        await scheduler_service._retry_failed_notifications()
        
        mock_notification_service.retry_failed_notifications.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_class_reminders(self, scheduler_service, mock_client_service, mock_subscription_service):
        """Тест отправки ежедневных напоминаний о занятиях."""
        await scheduler_service._send_class_reminders()
        
        mock_client_service.get_active_clients.assert_called_once()
        mock_subscription_service.get_client_subscriptions.assert_called()
    
    @pytest.mark.asyncio
    async def test_check_expiring_subscriptions(self, scheduler_service, mock_subscription_service):
        """Тест проверки истекающих абонементов."""
        # Настраиваем абонемент, истекающий скоро
        expiring_subscription = Subscription(
            id="expiring-subscription",
            client_id="test-client-1",
            type=SubscriptionType.PACKAGE_8,
            total_classes=8,
            used_classes=2,
            price=9600,
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=2)).date(),  # Истекает через 2 дня
            created_at=datetime.now()
        )
        
        mock_subscription_service.get_all_subscriptions.return_value = [expiring_subscription]
        
        await scheduler_service._check_expiring_subscriptions()
        
        mock_subscription_service.get_all_subscriptions.assert_called_once()


class TestNotificationSending:
    """Тесты отправки уведомлений."""
    
    @pytest.mark.asyncio
    async def test_send_single_class_reminder(self, scheduler_service, mock_client_service, mock_notification_service):
        """Тест отправки напоминания о конкретном занятии."""
        client_id = "test-client-1"
        class_date = datetime.now() + timedelta(hours=2)
        class_type = "Хатха-йога"
        
        await scheduler_service._send_single_class_reminder(client_id, class_date, class_type)
        
        mock_client_service.get_client.assert_called_once_with(client_id)
        mock_notification_service.create_notification.assert_called_once()
        mock_notification_service.send_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_subscription_expiry_reminder(self, scheduler_service, mock_subscription_service, mock_client_service, mock_notification_service):
        """Тест отправки напоминания об истечении абонемента."""
        subscription_id = "test-subscription-1"
        
        await scheduler_service._send_subscription_expiry_reminder(subscription_id)
        
        mock_subscription_service.get_subscription.assert_called_once_with(subscription_id)
        mock_client_service.get_client.assert_called_once()
        mock_notification_service.create_notification.assert_called_once()
        mock_notification_service.send_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_daily_schedule_reminder(self, scheduler_service, mock_client_service, mock_notification_service):
        """Тест отправки ежедневного напоминания о расписании."""
        client_id = "test-client-1"
        date = datetime.now() + timedelta(days=1)
        
        await scheduler_service._send_daily_schedule_reminder(client_id, date)
        
        mock_client_service.get_client.assert_called_once_with(client_id)
        mock_notification_service.create_notification.assert_called_once()
        mock_notification_service.send_notification.assert_called_once()


class TestScheduleGeneration:
    """Тесты генерации расписания."""
    
    def test_get_schedule_for_day_monday(self, scheduler_service):
        """Тест получения расписания для понедельника."""
        schedule = scheduler_service._get_schedule_for_day(0)  # Понедельник
        
        assert "Хатха-йога" in schedule
        assert "Виньяса-флоу" in schedule
        assert "Йога-нидра" in schedule
    
    def test_get_schedule_for_day_weekend(self, scheduler_service):
        """Тест получения расписания для выходных."""
        saturday_schedule = scheduler_service._get_schedule_for_day(5)  # Суббота
        sunday_schedule = scheduler_service._get_schedule_for_day(6)    # Воскресенье
        
        assert "Семейная йога" in saturday_schedule
        assert "Медитативная практика" in sunday_schedule
    
    def test_get_schedule_for_invalid_day(self, scheduler_service):
        """Тест получения расписания для некорректного дня."""
        schedule = scheduler_service._get_schedule_for_day(10)  # Некорректный день
        
        assert schedule == "Расписание уточняется"


class TestErrorHandling:
    """Тесты обработки ошибок."""
    
    @pytest.mark.asyncio
    async def test_start_scheduler_error(self, scheduler_service):
        """Тест обработки ошибки при запуске планировщика."""
        with patch.object(scheduler_service._scheduler, 'start', side_effect=Exception("Start error")):
            with pytest.raises(Exception, match="Start error"):
                await scheduler_service.start()
    
    @pytest.mark.asyncio
    async def test_notification_sending_error(self, scheduler_service, mock_client_service, mock_notification_service):
        """Тест обработки ошибки при отправке уведомления."""
        mock_client_service.get_client.side_effect = Exception("Client not found")
        
        # Не должно вызывать исключение, только логировать ошибку
        await scheduler_service._send_single_class_reminder("invalid-client", datetime.now(), "Test")
        
        mock_notification_service.create_notification.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_periodic_task_error_handling(self, scheduler_service, mock_notification_service):
        """Тест обработки ошибок в периодических задачах."""
        mock_notification_service.process_scheduled_notifications.side_effect = Exception("Processing error")
        
        # Не должно вызывать исключение
        await scheduler_service._process_scheduled_notifications()
        
        mock_notification_service.process_scheduled_notifications.assert_called_once() 