"""
📋 Pydantic модели для REST API

Схемы для валидации запросов и ответов.
Принцип CyberKitty: простота превыше всего.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
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
    """Запрос на создание клиента."""
    name: str = Field(..., min_length=2, max_length=100, description="Имя клиента")
    phone: str = Field(..., description="Телефон в формате +7XXXXXXXXXX")
    telegram_id: int = Field(..., description="Telegram ID")
    yoga_experience: bool = Field(..., description="Есть ли опыт йоги")
    intensity_preference: str = Field(..., description="Предпочтения по интенсивности")
    time_preference: str = Field(..., description="Предпочтения по времени")
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
    telegram_id: int
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


class ClientSearchRequest(BaseModel):
    """Запрос поиска клиентов."""
    query: Optional[str] = Field(None, max_length=100, description="Поисковый запрос")
    status: Optional[ClientStatus] = Field(None, description="Статус клиента")
    yoga_experience: Optional[bool] = Field(None, description="Опыт йоги")
    intensity_preference: Optional[str] = Field(None, description="Интенсивность")
    time_preference: Optional[str] = Field(None, description="Время")


# ===== АБОНЕМЕНТЫ =====

class SubscriptionCreateRequest(BaseModel):
    """Запрос на создание абонемента."""
    client_id: str = Field(..., description="ID клиента")
    subscription_type: SubscriptionType = Field(..., description="Тип абонемента")
    classes_total: int = Field(..., ge=1, le=50, description="Общее количество занятий")
    price_paid: float = Field(..., ge=0, description="Оплаченная сумма")
    payment_method: str = Field(..., max_length=50, description="Способ оплаты")
    notes: Optional[str] = Field(None, max_length=500, description="Заметки")


class SubscriptionResponse(BaseModel):
    """Ответ с данными абонемента."""
    id: str
    client_id: str
    subscription_type: SubscriptionType
    classes_total: int
    classes_used: int
    classes_remaining: int
    price_paid: float
    payment_method: str
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

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