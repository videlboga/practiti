"""
📝 Модели для регистрации и анкетирования CyberKitty Practiti

Модели для пошагового сбора данных от новых пользователей.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RegistrationState(Enum):
    """Состояния процесса регистрации."""
    START = "start"
    WAITING_NAME = "waiting_name"
    WAITING_PHONE = "waiting_phone"
    WAITING_AGE = "waiting_age"
    WAITING_YOGA_EXPERIENCE = "waiting_yoga_experience"
    WAITING_INTENSITY = "waiting_intensity"
    WAITING_TIME_PREFERENCE = "waiting_time_preference"
    WAITING_INJURIES = "waiting_injuries"
    WAITING_GOALS = "waiting_goals"
    WAITING_HOW_FOUND = "waiting_how_found"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"


class RegistrationData(BaseModel):
    """
    Временные данные регистрации пользователя.
    
    Собираются пошагово через Telegram Bot.
    """
    telegram_id: int
    telegram_username: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    yoga_experience: Optional[bool] = None
    intensity_preference: Optional[str] = None
    time_preference: Optional[str] = None
    injuries: Optional[str] = None
    goals: Optional[str] = None
    how_found_us: Optional[str] = None
    current_state: RegistrationState = RegistrationState.START
    
    @field_validator('phone')
    @classmethod
    def validate_phone_format(cls, v):
        """Валидация формата телефона."""
        if v is None:
            return v
        
        # Убираем все символы кроме цифр и +
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        
        # Проверяем формат
        if not cleaned.startswith('+'):
            if cleaned.startswith('8'):
                cleaned = '+7' + cleaned[1:]
            elif cleaned.startswith('7'):
                cleaned = '+' + cleaned
            else:
                cleaned = '+7' + cleaned
        
        # Проверяем длину
        if len(cleaned) != 12:  # +7XXXXXXXXXX
            raise ValueError("Телефон должен содержать 11 цифр")
        
        return cleaned
    
    @field_validator('age')
    @classmethod
    def validate_age_range(cls, v):
        """Валидация возраста."""
        if v is not None and (v < 16 or v > 80):
            raise ValueError("Возраст должен быть от 16 до 80 лет")
        return v
    
    def is_complete(self) -> bool:
        """Проверить, заполнены ли все обязательные поля."""
        required_fields = [
            'name', 'phone', 'yoga_experience', 
            'intensity_preference', 'time_preference'
        ]
        return all(getattr(self, field) is not None for field in required_fields)
    
    def get_summary(self) -> str:
        """Получить краткое резюме данных для подтверждения."""
        experience = "Да" if self.yoga_experience else "Нет"
        age_str = f"{self.age} лет" if self.age else "Не указан"
        injuries_str = self.injuries if self.injuries else "Нет"
        goals_str = self.goals if self.goals else "Не указаны"
        how_found_str = self.how_found_us if self.how_found_us else "Не указано"
        
        return f"""
📋 **Ваши данные:**

👤 **Имя:** {self.name}
📱 **Телефон:** {self.phone}
🎂 **Возраст:** {age_str}
🧘 **Опыт йоги:** {experience}
💪 **Интенсивность:** {self.intensity_preference}
⏰ **Время занятий:** {self.time_preference}
🩹 **Травмы/ограничения:** {injuries_str}
🎯 **Цели:** {goals_str}
📢 **Как узнали о нас:** {how_found_str}
        """.strip()


class RegistrationStep(BaseModel):
    """Информация о шаге регистрации."""
    state: RegistrationState
    question: str
    help_text: Optional[str] = None
    validation_error: Optional[str] = None
    options: Optional[list] = None  # Для кнопок выбора
    
    
# Конфигурация шагов регистрации
REGISTRATION_STEPS = {
    RegistrationState.WAITING_NAME: RegistrationStep(
        state=RegistrationState.WAITING_NAME,
        question="👤 Как вас зовут? Напишите ваше имя:",
        help_text="Введите ваше полное имя (например: Анна Петрова)"
    ),
    
    RegistrationState.WAITING_PHONE: RegistrationStep(
        state=RegistrationState.WAITING_PHONE,
        question="📱 Укажите ваш номер телефона:",
        help_text="Формат: +7XXXXXXXXXX или 8XXXXXXXXXX"
    ),
    
    RegistrationState.WAITING_AGE: RegistrationStep(
        state=RegistrationState.WAITING_AGE,
        question="🎂 Сколько вам лет?",
        help_text="Введите число от 16 до 80. Можете пропустить, отправив /skip"
    ),
    
    RegistrationState.WAITING_YOGA_EXPERIENCE: RegistrationStep(
        state=RegistrationState.WAITING_YOGA_EXPERIENCE,
        question="🧘 Есть ли у вас опыт занятий йогой?",
        help_text="Выберите один из вариантов:",
        options=["Да, есть опыт", "Нет, я новичок"]
    ),
    
    RegistrationState.WAITING_INTENSITY: RegistrationStep(
        state=RegistrationState.WAITING_INTENSITY,
        question="💪 Какую интенсивность занятий предпочитаете?",
        help_text="Выберите подходящий уровень:",
        options=["Низкая", "Средняя", "Высокая", "Любая"]
    ),
    
    RegistrationState.WAITING_TIME_PREFERENCE: RegistrationStep(
        state=RegistrationState.WAITING_TIME_PREFERENCE,
        question="⏰ В какое время вам удобно заниматься?",
        help_text="Выберите предпочтительное время:",
        options=["Утро", "День", "Вечер", "Любое"]
    ),
    
    RegistrationState.WAITING_INJURIES: RegistrationStep(
        state=RegistrationState.WAITING_INJURIES,
        question="🩹 Есть ли у вас травмы или ограничения?",
        help_text="Опишите кратко или отправьте /skip если нет"
    ),
    
    RegistrationState.WAITING_GOALS: RegistrationStep(
        state=RegistrationState.WAITING_GOALS,
        question="🎯 Какие у вас цели от занятий йогой?",
        help_text="Например: снять стресс, улучшить гибкость, похудеть. Можете пропустить /skip"
    ),
    
    RegistrationState.WAITING_HOW_FOUND: RegistrationStep(
        state=RegistrationState.WAITING_HOW_FOUND,
        question="📢 Как вы узнали о нашей студии?",
        help_text="Можете пропустить этот вопрос, отправив /skip",
        options=["Социальные сети", "Рекомендация друзей", "Поиск в интернете", "Реклама", "Другое"]
    )
} 