"""
💬 Модель обратной связи CyberKitty Practiti

Модель для сбора отзывов и обратной связи от клиентов после занятий.
Используется в post-class автоматизации.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class FeedbackType(str, Enum):
    """Типы обратной связи."""
    POST_CLASS = "post_class"           # После занятия
    SUBSCRIPTION_END = "subscription_end"  # После окончания абонемента
    GENERAL = "general"                 # Общая обратная связь
    COMPLAINT = "complaint"             # Жалоба
    SUGGESTION = "suggestion"           # Предложение


class FeedbackStatus(str, Enum):
    """Статусы обратной связи."""
    PENDING = "pending"                 # Ожидает ответа
    SUBMITTED = "submitted"             # Отправлена
    REVIEWED = "reviewed"               # Просмотрена
    RESPONDED = "responded"             # Получен ответ


class Feedback(BaseModel):
    """
    Основная модель обратной связи.
    
    Хранит отзывы клиентов о занятиях и услугах студии.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Уникальный ID обратной связи")
    client_id: str = Field(..., description="ID клиента")
    type: FeedbackType = Field(..., description="Тип обратной связи")
    status: FeedbackStatus = Field(default=FeedbackStatus.PENDING, description="Статус обратной связи")
    
    # Основные поля
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Оценка от 1 до 5")
    comment: Optional[str] = Field(default=None, max_length=1000, description="Комментарий клиента")
    
    # Связанные объекты
    booking_id: Optional[str] = Field(default=None, description="ID записи на занятие (если применимо)")
    subscription_id: Optional[str] = Field(default=None, description="ID абонемента (если применимо)")
    
    # Детальная оценка (для post-class feedback)
    class_rating: Optional[int] = Field(default=None, ge=1, le=5, description="Оценка занятия")
    teacher_rating: Optional[int] = Field(default=None, ge=1, le=5, description="Оценка преподавателя")
    studio_rating: Optional[int] = Field(default=None, ge=1, le=5, description="Оценка студии")
    
    # Дополнительные вопросы
    would_recommend: Optional[bool] = Field(default=None, description="Порекомендовал бы друзьям")
    difficulty_level: Optional[str] = Field(default=None, description="Уровень сложности (легко/нормально/сложно)")
    favorite_part: Optional[str] = Field(default=None, max_length=500, description="Что больше всего понравилось")
    improvement_suggestions: Optional[str] = Field(default=None, max_length=500, description="Предложения по улучшению")
    
    # Метаданные
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные данные")
    
    # Временные метки
    created_at: datetime = Field(default_factory=datetime.now, description="Дата создания")
    submitted_at: Optional[datetime] = Field(default=None, description="Дата отправки")
    reviewed_at: Optional[datetime] = Field(default=None, description="Дата просмотра")
    
    @field_validator('rating', 'class_rating', 'teacher_rating', 'studio_rating')
    @classmethod
    def validate_rating(cls, v: Optional[int]) -> Optional[int]:
        """Валидация оценок."""
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Оценка должна быть от 1 до 5')
        return v
    
    @field_validator('difficulty_level')
    @classmethod
    def validate_difficulty_level(cls, v: Optional[str]) -> Optional[str]:
        """Валидация уровня сложности."""
        if v is not None:
            allowed_levels = ['легко', 'нормально', 'сложно']
            if v.lower() not in allowed_levels:
                raise ValueError(f'Уровень сложности должен быть одним из: {", ".join(allowed_levels)}')
            return v.lower()
        return v
    
    @property
    def overall_rating(self) -> Optional[float]:
        """Общая оценка на основе всех рейтингов."""
        ratings = [r for r in [self.class_rating, self.teacher_rating, self.studio_rating] if r is not None]
        if not ratings:
            return self.rating
        
        if self.rating is not None:
            ratings.append(self.rating)
        
        return sum(ratings) / len(ratings) if ratings else None
    
    @property
    def is_positive(self) -> Optional[bool]:
        """Является ли отзыв положительным."""
        overall = self.overall_rating
        if overall is None:
            return None
        return overall >= 4.0
    
    @property
    def is_complete(self) -> bool:
        """Заполнена ли обратная связь полностью."""
        if self.type == FeedbackType.POST_CLASS:
            return (
                self.rating is not None and
                self.comment is not None and
                len(self.comment.strip()) > 0
            )
        return self.comment is not None and len(self.comment.strip()) > 0

    def __str__(self) -> str:
        """Строковое представление обратной связи."""
        rating_str = f" ({self.rating}★)" if self.rating else ""
        return f"Feedback({self.type.value}{rating_str})"
    
    def __repr__(self) -> str:
        """Repr представление обратной связи."""
        return f"Feedback(id={self.id}, client_id={self.client_id}, type={self.type})"


class FeedbackCreateData(BaseModel):
    """
    Данные для создания новой обратной связи.
    
    Используется при запросе отзыва от клиента.
    """
    
    client_id: str = Field(..., description="ID клиента")
    type: FeedbackType = Field(..., description="Тип обратной связи")
    booking_id: Optional[str] = Field(default=None, description="ID записи на занятие")
    subscription_id: Optional[str] = Field(default=None, description="ID абонемента")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные данные")


class FeedbackUpdateData(BaseModel):
    """
    Данные для обновления обратной связи.
    
    Используется когда клиент заполняет форму обратной связи.
    """
    
    status: Optional[FeedbackStatus] = Field(default=None, description="Статус обратной связи")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Общая оценка")
    comment: Optional[str] = Field(default=None, max_length=1000, description="Комментарий")
    
    # Детальные оценки
    class_rating: Optional[int] = Field(default=None, ge=1, le=5, description="Оценка занятия")
    teacher_rating: Optional[int] = Field(default=None, ge=1, le=5, description="Оценка преподавателя")
    studio_rating: Optional[int] = Field(default=None, ge=1, le=5, description="Оценка студии")
    
    # Дополнительные вопросы
    would_recommend: Optional[bool] = Field(default=None, description="Порекомендовал бы друзьям")
    difficulty_level: Optional[str] = Field(default=None, description="Уровень сложности")
    favorite_part: Optional[str] = Field(default=None, max_length=500, description="Что понравилось")
    improvement_suggestions: Optional[str] = Field(default=None, max_length=500, description="Предложения")
    
    # Валидаторы
    _validate_rating = field_validator('rating', 'class_rating', 'teacher_rating', 'studio_rating')(
        Feedback.validate_rating.__func__
    )
    _validate_difficulty = field_validator('difficulty_level')(Feedback.validate_difficulty_level.__func__)


class FeedbackSummary(BaseModel):
    """
    Сводка по обратной связи.
    
    Используется для аналитики и отчетов.
    """
    
    total_feedback: int = Field(..., description="Общее количество отзывов")
    average_rating: Optional[float] = Field(default=None, description="Средняя оценка")
    positive_feedback_percentage: float = Field(..., description="Процент положительных отзывов")
    
    # Детальная статистика
    rating_distribution: Dict[int, int] = Field(default_factory=dict, description="Распределение оценок")
    common_complaints: list[str] = Field(default_factory=list, description="Частые жалобы")
    common_compliments: list[str] = Field(default_factory=list, description="Частые похвалы")
    
    # По типам
    post_class_count: int = Field(default=0, description="Количество отзывов после занятий")
    general_count: int = Field(default=0, description="Количество общих отзывов")
    
    # Временной период
    period_start: datetime = Field(..., description="Начало периода")
    period_end: datetime = Field(..., description="Конец периода") 