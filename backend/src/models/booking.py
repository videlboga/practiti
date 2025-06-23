"""
📅 Модель записи на занятие CyberKitty Practiti

Модель для управления записями клиентов на занятия йогой.
Соответствует контракту BOOKING CONTRACT из архитектуры.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class BookingStatus(str, Enum):
    """Статусы записи на занятие."""
    SCHEDULED = "scheduled"           # Запланирована
    CONFIRMED = "confirmed"           # Подтверждена
    ATTENDED = "attended"             # Клиент пришёл
    MISSED = "missed"                 # Клиент не пришёл
    CANCELLED = "cancelled"           # Отменена


class Booking(BaseModel):
    """
    Основная модель записи на занятие.
    
    Соответствует BOOKING CONTRACT из архитектуры.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Уникальный ID записи")
    client_id: str = Field(..., description="ID клиента")
    class_date: datetime = Field(..., description="Дата и время занятия")
    class_type: str = Field(..., description="Тип занятия (хатха, виньяса, и т.д.)")
    status: BookingStatus = Field(default=BookingStatus.SCHEDULED, description="Статус записи")
    created_at: datetime = Field(default_factory=datetime.now, description="Дата создания записи")
    
    # Дополнительные поля
    subscription_id: Optional[str] = Field(default=None, description="ID абонемента (если применимо)")
    teacher_name: Optional[str] = Field(default=None, description="Имя преподавателя")
    class_duration: int = Field(default=90, ge=30, le=180, description="Длительность занятия в минутах")
    notes: Optional[str] = Field(default=None, max_length=500, description="Заметки к записи")
    
    # Поля для отслеживания изменений
    confirmed_at: Optional[datetime] = Field(default=None, description="Дата подтверждения")
    attended_at: Optional[datetime] = Field(default=None, description="Дата посещения")
    cancelled_at: Optional[datetime] = Field(default=None, description="Дата отмены")
    
    @field_validator('class_date')
    @classmethod
    def validate_class_date(cls, v: datetime) -> datetime:
        """Валидация даты занятия (поддержка aware/naive)."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        # Приводим оба значения к UTC naïve для корректного сравнения
        if v.tzinfo is not None:
            v_cmp = v.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            v_cmp = v
        if now.tzinfo is not None:
            now_cmp = now.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            now_cmp = now
        if v_cmp < now_cmp:
            raise ValueError('Нельзя записаться на занятие в прошлом')
        return v
    
    @field_validator('class_type')
    @classmethod
    def validate_class_type(cls, v: str) -> str:
        """Валидация типа занятия (MVP: допускаем любой не пустой тип)."""
        return v.strip()
    
    @property
    def is_upcoming(self) -> bool:
        """Проверка, что занятие предстоящее."""
        return self.class_date > datetime.now()
    
    @property
    def is_past(self) -> bool:
        """Проверка, что занятие уже прошло."""
        return self.class_date < datetime.now()
    
    @property
    def can_be_cancelled(self) -> bool:
        """Можно ли отменить запись."""
        # Можно отменить только запланированные или подтверждённые записи
        # И только если до занятия больше 2 часов
        if self.status not in [BookingStatus.SCHEDULED, BookingStatus.CONFIRMED]:
            return False
        
        time_until_class = (self.class_date - datetime.now()).total_seconds()
        return time_until_class > 7200  # 2 часа = 7200 секунд

    def __str__(self) -> str:
        """Строковое представление записи."""
        return f"Booking({self.class_type}, {self.class_date.strftime('%Y-%m-%d %H:%M')})"
    
    def __repr__(self) -> str:
        """Repr представление записи."""
        return f"Booking(id={self.id}, client_id={self.client_id}, status={self.status})"


class BookingCreateData(BaseModel):
    """
    Данные для создания новой записи.
    
    Используется при записи клиента на занятие.
    """
    
    client_id: str = Field(..., description="ID клиента")
    class_date: datetime = Field(..., description="Дата и время занятия")
    class_type: str = Field(..., description="Тип занятия")
    subscription_id: Optional[str] = Field(default=None, description="ID абонемента")
    teacher_name: Optional[str] = Field(default=None, description="Имя преподавателя")
    class_duration: int = Field(default=90, ge=30, le=180, description="Длительность занятия")
    notes: Optional[str] = Field(default=None, max_length=500, description="Заметки к записи")
    
    # Наследуем валидаторы от основной модели
    _validate_class_date = field_validator('class_date')(Booking.validate_class_date.__func__)
    _validate_class_type = field_validator('class_type')(Booking.validate_class_type.__func__)


class BookingUpdateData(BaseModel):
    """
    Данные для обновления существующей записи.
    
    Все поля опциональные - обновляются только переданные.
    """
    
    class_date: Optional[datetime] = Field(default=None, description="Дата и время занятия")
    class_type: Optional[str] = Field(default=None, description="Тип занятия")
    status: Optional[BookingStatus] = Field(default=None, description="Статус записи")
    teacher_name: Optional[str] = Field(default=None, description="Имя преподавателя")
    class_duration: Optional[int] = Field(default=None, ge=30, le=180, description="Длительность занятия")
    notes: Optional[str] = Field(default=None, max_length=500, description="Заметки к записи")
    
    @field_validator('class_date')
    @classmethod
    def validate_class_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Валидация даты занятия."""
        if v is not None:
            return Booking.validate_class_date(v)
        return v
    
    @field_validator('class_type')
    @classmethod
    def validate_class_type(cls, v: Optional[str]) -> Optional[str]:
        """Валидация типа занятия."""
        if v is not None:
            return Booking.validate_class_type(v)
        return v 