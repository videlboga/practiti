"""
🕐 Протокол сервиса планировщика задач

Определяет интерфейс для управления автоматическими напоминаниями и фоновыми задачами.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any


class SchedulerServiceProtocol(ABC):
    """
    Протокол сервиса планировщика задач.
    
    Определяет интерфейс для:
    - Управления планировщиком
    - Планирования напоминаний
    - Управления заданиями
    """
    
    @abstractmethod
    async def start(self) -> None:
        """Запуск планировщика и регистрация периодических задач."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Остановка планировщика."""
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """
        Отменить запланированное задание.
        
        Args:
            job_id: ID задания
            
        Returns:
            True если задание отменено успешно
        """
        pass
    
    @abstractmethod
    async def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """
        Получить список запланированных заданий.
        
        Returns:
            Список заданий с информацией
        """
        pass 