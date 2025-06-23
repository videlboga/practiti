"""
📋 Pydantic модели для REST API

Схемы для валидации запросов и ответов.
Принцип CyberKitty: простота превыше всего.
"""

from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from ..models.client import ClientStatus
from ..models.subscription import SubscriptionType, SubscriptionStatus
from ..models.notification import NotificationType, NotificationStatus, NotificationPriority


# ===== ОБЩИЕ МОДЕЛИ =====

class APIResponse(BaseModel):
    """Базовая модель ответа API."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class PaginationParams(BaseModel):
    """Параметры пагинации."""
    page: int = Field(1, ge=1, description="Номер страницы")
    limit: int = Field(20, ge=1, le=100, description="Количество элементов на странице")


class PaginatedResponse(BaseModel):
    """Ответ с пагинацией."""
    items: List[Any]
    total: int
    page: int
    limit: int
    pages: int


# ===== КЛИЕНТЫ =====

class ClientCreateRequest(BaseModel):
    """Запрос на создание клиента (админка)."""

    name: str = Field(..., min_length=2, max_length=100, description="Имя клиента")
    phone: str = Field(..., description="Телефон в формате +7XXXXXXXXXX")

    # Необязательные
    telegram_id: Optional[int] = Field(None, description="Telegram ID")
    yoga_experience: bool = Field(False, description="Есть ли опыт йоги")
    intensity_preference: str = Field("любая", description="Предпочтения по интенсивности")
    time_preference: str = Field("любое", description="Предпочтения по времени")

    # Дополнительные поля
    age: Optional[int] = Field(None, ge=16, le=100, description="Возраст")
    injuries: Optional[str] = Field(None, max_length=500, description="Травмы и ограничения")
    goals: Optional[str] = Field(None, max_length=500, description="Цели занятий")
    how_found_us: Optional[str] = Field(None, max_length=200, description="Как узнал о студии")


class ClientUpdateRequest(BaseModel):
    """Запрос на обновление клиента."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, description="Телефон")
    yoga_experience: Optional[bool] = None
    intensity_preference: Optional[str] = None
    time_preference: Optional[str] = None
    age: Optional[int] = Field(None, ge=16, le=100)
    injuries: Optional[str] = Field(None, max_length=500)
    goals: Optional[str] = Field(None, max_length=500)
    how_found_us: Optional[str] = Field(None, max_length=200)
    status: Optional[ClientStatus] = None


class ClientResponse(BaseModel):
    """Ответ с данными клиента."""
    id: str
    name: str
    phone: str
    telegram_id: Optional[str | int] = None
    yoga_experience: bool
    intensity_preference: str
    time_preference: str
    age: Optional[int]
    injuries: Optional[str]
    goals: Optional[str]
    how_found_us: Optional[str]
    status: ClientStatus
    created_at: datetime

    class Config:
        from_attributes = True

    # допускаем '', None -> None; строки с цифрами -> int
    @field_validator('telegram_id', mode='before')
    def _validate_telegram_id(cls, v):  # noqa: D401
        if v in (None, '', 'null', 'None'):
            return None
        # допускаем как строку, так и int
        try:
            return int(v)
        except (ValueError, TypeError):
            return str(v) if v is not None else None


class ClientSearchRequest(BaseModel):
    """Запрос поиска клиентов."""
    query: Optional[str] = Field(None, max_length=100, description="Поисковый запрос")
    status: Optional[ClientStatus] = Field(None, description="Статус клиента")
    yoga_experience: Optional[bool] = Field(None, description="Опыт йоги")
    intensity_preference: Optional[str] = Field(None, description="Интенсивность")
    time_preference: Optional[str] = Field(None, description="Время")


# ===== АБОНЕМЕНТЫ =====

class SubscriptionCreateRequest(BaseModel):
    """Запрос на создание абонемента (упрощён для MVP)."""

    client_id: str = Field(..., description="ID клиента")
    subscription_type: SubscriptionType = Field(..., description="Тип абонемента")

    # Поля ниже сделаны необязательными, чтобы фронтенд мог отправлять
    # только минимальный набор данных. При необходимости бизнес-логика
    # может проставить значения по-умолчанию.
    classes_total: Optional[int] = Field(None, ge=1, le=50, description="Общее количество занятий")
    price_paid: Optional[float] = Field(None, ge=0, description="Оплаченная сумма")
    payment_method: Optional[str] = Field(None, max_length=50, description="Способ оплаты")
    notes: Optional[str] = Field(None, max_length=500, description="Заметки")


class SubscriptionResponse(BaseModel):
    """Ответ с данными абонемента."""
    id: str
    client_id: str
    type: SubscriptionType
    total_classes: int
    used_classes: int
    remaining_classes: int
    start_date: date
    end_date: date
    status: SubscriptionStatus
    created_at: datetime
    price: int
    payment_confirmed: bool
    payment_confirmed_at: Optional[datetime]

    class Config:
        from_attributes = True


class UseClassRequest(BaseModel):
    """Запрос на использование занятия."""
    subscription_id: str = Field(..., description="ID абонемента")
    class_date: datetime = Field(..., description="Дата и время занятия")
    class_type: str = Field(..., max_length=100, description="Тип занятия")
    instructor: Optional[str] = Field(None, max_length=100, description="Инструктор")
    notes: Optional[str] = Field(None, max_length=500, description="Заметки")


# ===== УВЕДОМЛЕНИЯ =====

class NotificationCreateRequest(BaseModel):
    """Запрос на создание уведомления."""
    client_id: str = Field(..., description="ID клиента")
    notification_type: NotificationType = Field(..., description="Тип уведомления")
    title: str = Field(..., min_length=1, max_length=200, description="Заголовок")
    message: str = Field(..., min_length=1, max_length=1000, description="Сообщение")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="Приоритет")
    scheduled_at: Optional[datetime] = Field(None, description="Время отправки")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные")


class NotificationResponse(BaseModel):
    """Ответ с данными уведомления."""
    id: str
    client_id: str
    notification_type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    status: NotificationStatus
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    failed_at: Optional[datetime]
    retry_count: int
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_notification(cls, notification):
        """Создать response из доменной модели Notification."""
        return cls(
            id=notification.id,
            client_id=notification.client_id,
            notification_type=notification.type,  # Преобразуем type -> notification_type
            title=notification.title,
            message=notification.message,
            priority=notification.priority,
            status=notification.status,
            scheduled_at=notification.scheduled_at,
            sent_at=notification.sent_at,
            delivered_at=notification.delivered_at,
            failed_at=notification.failed_at,
            retry_count=notification.retry_count,
            metadata=notification.metadata,
            created_at=notification.created_at,
            updated_at=notification.updated_at
        )


class NotificationSearchRequest(BaseModel):
    """Запрос поиска уведомлений."""
    client_id: Optional[str] = Field(None, description="ID клиента")
    notification_type: Optional[NotificationType] = Field(None, description="Тип уведомления")
    status: Optional[NotificationStatus] = Field(None, description="Статус")
    priority: Optional[NotificationPriority] = Field(None, description="Приоритет")
    date_from: Optional[datetime] = Field(None, description="Дата от")
    date_to: Optional[datetime] = Field(None, description="Дата до")


# ===== АНАЛИТИКА =====

class AnalyticsResponse(BaseModel):
    """Ответ с аналитическими данными."""
    period: str
    data: Dict[str, Any]
    generated_at: datetime


class ClientStatsResponse(BaseModel):
    """Статистика по клиентам."""
    total_clients: int
    active_clients: int
    new_clients_this_month: int
    clients_by_experience: Dict[str, int]
    clients_by_status: Dict[str, int]


class SubscriptionStatsResponse(BaseModel):
    """Статистика по абонементам."""
    total_subscriptions: int
    active_subscriptions: int
    revenue_this_month: float
    subscriptions_by_type: Dict[str, int]
    average_subscription_value: float


class NotificationStatsResponse(BaseModel):
    """Статистика по уведомлениям."""
    total_notifications: int
    sent_notifications: int
    delivered_notifications: int
    failed_notifications: int
    delivery_rate: float
    notifications_by_type: Dict[str, int]


# ===== БРОНИРОВАНИЯ =====

class BookingCreateRequest(BaseModel):
    """Запрос на создание записи на занятие."""

    client_id: str = Field(..., description="ID клиента")
    class_date: datetime = Field(..., description="Дата и время занятия")
    class_type: str = Field(..., description="Тип занятия")
    subscription_id: Optional[str] = Field(None, description="ID абонемента")
    teacher_name: Optional[str] = Field(None, description="Имя преподавателя")
    class_duration: int = Field(90, ge=30, le=180, description="Длительность занятия")
    notes: Optional[str] = Field(None, max_length=500, description="Заметки")

    def to_model(self):  # pragma: no cover
        """Конвертация в доменную модель BookingCreateData."""
        from ..models.booking import BookingCreateData

        return BookingCreateData.model_validate(self.model_dump())


class BookingResponse(BaseModel):
    """Ответ с информацией о бронировании."""

    id: str
    client_id: str
    class_date: datetime
    class_type: str
    status: str
    subscription_id: Optional[str]
    teacher_name: Optional[str]
    class_duration: int
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BookingUpdateRequest(BaseModel):
    """Запрос на обновление записи на занятие (частичное)."""

    class_date: Optional[datetime] = Field(None, description="Дата и время занятия")
    class_type: Optional[str] = Field(None, description="Тип занятия")
    status: Optional[str] = Field(None, description="Статус записи")
    teacher_name: Optional[str] = Field(None, description="Имя преподавателя")
    class_duration: Optional[int] = Field(None, ge=30, le=180, description="Длительность занятия")
    notes: Optional[str] = Field(None, max_length=500, description="Заметки")

    def to_update_data(self):  # pragma: no cover
        from ..models.booking import BookingUpdateData
        return BookingUpdateData.model_validate(self.model_dump(exclude_unset=True)) 