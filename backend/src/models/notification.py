"""
📢 Модель уведомлений Practiti

Модель для управления уведомлениями и напоминаниями клиентов йога-студии.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Типы уведомлений."""
    SUBSCRIPTION_EXPIRING = "subscription_expiring"      # Абонемент скоро истекает
    SUBSCRIPTION_EXPIRED = "subscription_expired"        # Абонемент истек
    CLASSES_RUNNING_OUT = "classes_running_out"          # Заканчиваются занятия
    PAYMENT_REMINDER = "payment_reminder"               # Напоминание об оплате
    CLASS_REMINDER = "class_reminder"                   # Напоминание о занятии
    WELCOME_MESSAGE = "welcome_message"                 # Приветственное сообщение
    REGISTRATION_COMPLETE = "registration_complete"      # Регистрация завершена
    SUBSCRIPTION_PURCHASED = "subscription_purchased"    # Абонемент куплен
    GENERAL_INFO = "general_info"                       # Общая информация


class NotificationStatus(str, Enum):
    """Статусы уведомлений."""
    PENDING = "pending"        # Ожидает отправки
    SENT = "sent"             # Отправлено
    DELIVERED = "delivered"    # Доставлено
    FAILED = "failed"         # Ошибка отправки
    CANCELLED = "cancelled"    # Отменено


class NotificationPriority(str, Enum):
    """Приоритеты уведомлений."""
    LOW = "low"           # Низкий приоритет
    NORMAL = "normal"     # Обычный приоритет
    HIGH = "high"         # Высокий приоритет
    URGENT = "urgent"     # Срочное уведомление


class NotificationChannel(str, Enum):
    """Канал отправки уведомления."""
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"


class Notification(BaseModel):
    """
    Основная модель уведомления.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Уникальный ID уведомления")
    client_id: str = Field(..., description="ID клиента-получателя")
    type: NotificationType = Field(..., description="Тип уведомления")
    title: str = Field(..., max_length=200, description="Заголовок уведомления")
    message: str = Field(..., max_length=2000, description="Текст уведомления")
    
    # Статус и приоритет
    status: NotificationStatus = Field(default=NotificationStatus.PENDING, description="Статус уведомления")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="Приоритет")
    
    # Временные метки
    created_at: datetime = Field(default_factory=datetime.now, description="Дата создания")
    updated_at: datetime = Field(default_factory=datetime.now, description="Дата обновления")
    scheduled_at: Optional[datetime] = Field(default=None, description="Запланированное время отправки")
    sent_at: Optional[datetime] = Field(default=None, description="Время отправки")
    delivered_at: Optional[datetime] = Field(default=None, description="Время доставки")
    failed_at: Optional[datetime] = Field(default=None, description="Время ошибки отправки")
    
    # Дополнительные данные
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные данные")
    telegram_message_id: Optional[int] = Field(default=None, description="ID сообщения в Telegram")
    
    # Настройки повтора
    retry_count: int = Field(default=0, ge=0, description="Количество попыток отправки")
    max_retries: int = Field(default=3, ge=0, description="Максимальное количество попыток")
    
    # Канал отправки
    channel: NotificationChannel = Field(default=NotificationChannel.TELEGRAM, description="Канал отправки уведомления")
    
    def __str__(self) -> str:
        """Строковое представление уведомления."""
        return f"Notification({self.type.value}, {self.status.value})"
    
    def __repr__(self) -> str:
        """Repr представление уведомления."""
        return f"Notification(id={self.id}, type={self.type}, status={self.status}, client_id={self.client_id})"


class NotificationCreateData(BaseModel):
    """
    Данные для создания нового уведомления.
    """
    
    client_id: str = Field(..., description="ID клиента-получателя")
    type: NotificationType = Field(..., description="Тип уведомления")
    title: str = Field(..., max_length=200, description="Заголовок уведомления")
    message: str = Field(..., max_length=2000, description="Текст уведомления")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="Приоритет")
    scheduled_at: Optional[datetime] = Field(default=None, description="Запланированное время отправки")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные данные")
    channel: NotificationChannel = Field(default=NotificationChannel.TELEGRAM, description="Канал отправки уведомления")


class NotificationUpdateData(BaseModel):
    """
    Данные для обновления существующего уведомления.
    """
    
    status: Optional[NotificationStatus] = Field(default=None, description="Статус уведомления")
    sent_at: Optional[datetime] = Field(default=None, description="Время отправки")
    delivered_at: Optional[datetime] = Field(default=None, description="Время доставки")
    failed_at: Optional[datetime] = Field(default=None, description="Время ошибки отправки")
    telegram_message_id: Optional[int] = Field(default=None, description="ID сообщения в Telegram")
    retry_count: Optional[int] = Field(default=None, ge=0, description="Количество попыток отправки")
    updated_at: Optional[datetime] = Field(default_factory=datetime.now, description="Время обновления")
    channel: Optional[NotificationChannel] = Field(default=None, description="Канал отправки уведомления")


class NotificationTemplate(BaseModel):
    """
    Шаблон уведомления для разных типов.
    """
    
    type: NotificationType = Field(..., description="Тип уведомления")
    title_template: str = Field(..., description="Шаблон заголовка")
    message_template: str = Field(..., description="Шаблон сообщения")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="Приоритет по умолчанию")
    
    def format_notification(self, **kwargs) -> tuple[str, str]:
        """
        Форматирует шаблон с переданными данными.
        
        Args:
            **kwargs: Данные для подстановки в шаблон
            
        Returns:
            Кортеж (заголовок, сообщение)
        """
        try:
            title = self.title_template.format(**kwargs)
            message = self.message_template.format(**kwargs)
            return title, message
        except KeyError as e:
            raise ValueError(f"Отсутствует обязательный параметр для шаблона: {e}")


# Предустановленные шаблоны уведомлений
NOTIFICATION_TEMPLATES = {
    NotificationType.SUBSCRIPTION_EXPIRING: NotificationTemplate(
        type=NotificationType.SUBSCRIPTION_EXPIRING,
        title_template="⏰ Ваш абонемент скоро истекает",
        message_template="Привет, {client_name}! 👋\n\nВаш абонемент «{subscription_type}» истекает {end_date}.\n\nОсталось занятий: {remaining_classes}\n\n💡 Рекомендуем продлить абонемент заранее!",
        priority=NotificationPriority.HIGH
    ),
    
    NotificationType.SUBSCRIPTION_EXPIRED: NotificationTemplate(
        type=NotificationType.SUBSCRIPTION_EXPIRED,
        title_template="❌ Ваш абонемент истек",
        message_template="Привет, {client_name}! 👋\n\nВаш абонемент «{subscription_type}» истек {end_date}.\n\n🔄 Для продолжения занятий приобретите новый абонемент.",
        priority=NotificationPriority.HIGH
    ),
    
    NotificationType.CLASSES_RUNNING_OUT: NotificationTemplate(
        type=NotificationType.CLASSES_RUNNING_OUT,
        title_template="⚠️ Заканчиваются занятия",
        message_template="Привет, {client_name}! 👋\n\nНа вашем абонементе осталось всего {remaining_classes} занятий.\n\n💡 Рекомендуем приобрести новый абонемент!",
        priority=NotificationPriority.NORMAL
    ),
    
    NotificationType.PAYMENT_REMINDER: NotificationTemplate(
        type=NotificationType.PAYMENT_REMINDER,
        title_template="💳 Напоминание об оплате",
        message_template="Привет, {client_name}! 👋\n\nНапоминаем об оплате абонемента «{subscription_type}».\n\nСумма: {price}₽\n\n📞 Свяжитесь с нами для оплаты!",
        priority=NotificationPriority.HIGH
    ),
    
    NotificationType.WELCOME_MESSAGE: NotificationTemplate(
        type=NotificationType.WELCOME_MESSAGE,
        title_template="🌟 Добро пожаловать в Practiti!",
        message_template="Привет, {client_name}! 👋\n\nДобро пожаловать в йога-студию Practiti! 🧘‍♀️\n\nМы рады видеть вас в нашем сообществе. Готовы начать путь к гармонии и здоровью?\n\n✨ Намасте!",
        priority=NotificationPriority.NORMAL
    ),
    
    NotificationType.REGISTRATION_COMPLETE: NotificationTemplate(
        type=NotificationType.REGISTRATION_COMPLETE,
        title_template="✅ Регистрация завершена",
        message_template="Отлично, {client_name}! 🎉\n\nВаша регистрация в Practiti успешно завершена.\n\n📱 Теперь вы можете:\n• Покупать абонементы\n• Записываться на занятия\n• Получать уведомления\n\nДобро пожаловать в нашу йога-семью! 🧘‍♀️",
        priority=NotificationPriority.NORMAL
    ),
    
    NotificationType.SUBSCRIPTION_PURCHASED: NotificationTemplate(
        type=NotificationType.SUBSCRIPTION_PURCHASED,
        title_template="🎫 Абонемент приобретен",
        message_template="Поздравляем, {client_name}! 🎉\n\nВы успешно приобрели абонемент «{subscription_type}».\n\n📋 Детали:\n• Занятий: {total_classes}\n• Действует до: {end_date}\n• Стоимость: {price}₽\n\nУвидимся на занятиях! 🧘‍♀️",
        priority=NotificationPriority.NORMAL
    ),
    
    NotificationType.CLASS_REMINDER: NotificationTemplate(
        type=NotificationType.CLASS_REMINDER,
        title_template="⏰ Напоминание о занятии",
        message_template="Привет, {client_name}! 👋\n\nНапоминаем о занятии «{class_type}» {class_date}.\n\n📍 Увидимся в зале! Не забудьте коврик 🧘‍♀️",
        priority=NotificationPriority.HIGH
    ),
    
    NotificationType.GENERAL_INFO: NotificationTemplate(
        type=NotificationType.GENERAL_INFO,
        title_template="ℹ️ Информация",
        message_template="Привет, {client_name}! 👋\n\n{message}",
        priority=NotificationPriority.LOW
    ),
} 