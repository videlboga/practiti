"""
🎫 Модель абонемента CyberKitty Practiti

Модель для управления абонементами клиентов студии йоги.
Соответствует контракту SUBSCRIPTION CONTRACT из архитектуры.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, computed_field


class SubscriptionType(str, Enum):
    """Типы абонементов."""
    TRIAL = "trial"                    # Пробный абонемент (500₽, 1 занятие, 14 дней)
    SINGLE = "single"                  # Разовое занятие (1100₽, 1 занятие)
    PACKAGE_4 = "package_4"           # 4 занятия (3200₽, 30 дней)
    PACKAGE_8 = "package_8"           # 8 занятий (7000₽, 30 дней)
    PACKAGE_12 = "package_12"         # 12 занятий (9000₽, 30 дней)
    UNLIMITED = "unlimited"           # Безлимитный (10800₽, 30 дней)


class SubscriptionStatus(str, Enum):
    """Статусы абонемента."""
    PENDING = "pending"               # Ожидает оплаты
    ACTIVE = "active"                 # Активный
    EXPIRED = "expired"               # Истёк
    EXHAUSTED = "exhausted"           # Исчерпан (закончились занятия)
    SUSPENDED = "suspended"           # Приостановлен
    CANCELLED = "cancelled"           # Отменён


class Subscription(BaseModel):
    """
    Основная модель абонемента.
    
    Соответствует SUBSCRIPTION CONTRACT из архитектуры.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Уникальный ID абонемента")
    client_id: str = Field(..., description="ID клиента-владельца")
    type: SubscriptionType = Field(..., description="Тип абонемента")
    total_classes: int = Field(..., ge=0, description="Общее количество занятий")
    used_classes: int = Field(default=0, ge=0, description="Использованные занятия")
    start_date: date = Field(..., description="Дата начала действия")
    end_date: date = Field(..., description="Дата окончания действия")
    status: SubscriptionStatus = Field(default=SubscriptionStatus.PENDING, description="Статус абонемента")
    
    # Дополнительные поля
    created_at: datetime = Field(default_factory=datetime.now, description="Дата создания")
    price: int = Field(..., ge=0, description="Цена абонемента в рублях")
    payment_confirmed: bool = Field(default=False, description="Подтверждена ли оплата")
    payment_confirmed_at: Optional[datetime] = Field(default=None, description="Дата подтверждения оплаты")
    
    @computed_field
    @property
    def remaining_classes(self) -> int:
        """Оставшееся количество занятий."""
        if self.type == SubscriptionType.UNLIMITED:
            return 999  # Безлимитный абонемент
        return max(0, self.total_classes - self.used_classes)
    
    @computed_field  
    @property
    def is_active(self) -> bool:
        """Проверка активности абонемента."""
        today = date.today()
        return (
            self.status == SubscriptionStatus.ACTIVE and
            self.start_date <= today <= self.end_date and
            self.remaining_classes > 0 and
            self.payment_confirmed
        )
    
    @computed_field
    @property 
    def is_expired(self) -> bool:
        """Проверка истечения абонемента."""
        return date.today() > self.end_date
    
    @computed_field
    @property
    def is_exhausted(self) -> bool:
        """Проверка исчерпания занятий."""
        return self.type != SubscriptionType.UNLIMITED and self.remaining_classes <= 0
    
    @field_validator('used_classes')
    @classmethod
    def validate_used_classes(cls, v: int, info) -> int:
        """Валидация использованных занятий."""
        if hasattr(info, 'data') and 'total_classes' in info.data:
            total_classes = info.data['total_classes']
            subscription_type = info.data.get('type')
            
            # Для безлимитного абонемента нет ограничений
            if subscription_type != SubscriptionType.UNLIMITED and v > total_classes:
                raise ValueError(f'Использованные занятия ({v}) не могут превышать общее количество ({total_classes})')
        
        return v
    
    @field_validator('end_date')
    @classmethod  
    def validate_end_date(cls, v: date, info) -> date:
        """Валидация даты окончания."""
        if hasattr(info, 'data') and 'start_date' in info.data:
            start_date = info.data['start_date']
            if v <= start_date:
                raise ValueError('Дата окончания должна быть позже даты начала')
        
        return v

    def __str__(self) -> str:
        """Строковое представление абонемента."""
        return f"Subscription({self.type.value}, {self.remaining_classes}/{self.total_classes})"
    
    def __repr__(self) -> str:
        """Repr представление абонемента."""
        return f"Subscription(id={self.id}, type={self.type}, status={self.status}, remaining={self.remaining_classes})"


class SubscriptionCreateData(BaseModel):
    """
    Данные для создания нового абонемента.
    
    Используется при покупке абонемента клиентом.
    """
    
    client_id: str = Field(..., description="ID клиента-владельца")
    type: SubscriptionType = Field(..., description="Тип абонемента")
    start_date: Optional[date] = Field(default=None, description="Дата начала (по умолчанию сегодня)")
    
    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v: Optional[date]) -> date:
        """Установка даты начала по умолчанию."""
        if v is None:
            return date.today()
        
        # Нельзя создать абонемент в прошлом
        if v < date.today():
            raise ValueError('Дата начала не может быть в прошлом')
        
        return v


class SubscriptionUpdateData(BaseModel):
    """
    Данные для обновления существующего абонемента.
    
    Все поля опциональные - обновляются только переданные.
    """
    
    status: Optional[SubscriptionStatus] = Field(default=None, description="Статус абонемента")
    used_classes: Optional[int] = Field(default=None, ge=0, description="Использованные занятия")
    payment_confirmed: Optional[bool] = Field(default=None, description="Подтверждена ли оплата")
    end_date: Optional[date] = Field(default=None, description="Дата окончания действия")
    
    @field_validator('used_classes')
    @classmethod
    def validate_used_classes(cls, v: Optional[int]) -> Optional[int]:
        """Валидация использованных занятий."""
        if v is not None and v < 0:
            raise ValueError('Использованные занятия не могут быть отрицательными')
        return v 