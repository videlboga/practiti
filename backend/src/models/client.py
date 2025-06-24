"""
👤 Модель клиента CyberKitty Practiti

Основная модель для хранения данных о клиентах студии йоги.
Соответствует контракту CLIENT CONTRACT из архитектуры.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class ClientStatus(str, Enum):
    """Статусы клиента."""
    ACTIVE = "active"           # Активный клиент
    INACTIVE = "inactive"       # Неактивный клиент  
    BLOCKED = "blocked"         # Заблокированный клиент
    TRIAL = "trial"            # Клиент на пробном периоде


class Client(BaseModel):
    """
    Основная модель клиента.
    
    Соответствует CLIENT CONTRACT из архитектуры.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Уникальный ID клиента")
    name: str = Field(..., min_length=2, max_length=100, description="Имя клиента")
    phone: str = Field(..., description="Номер телефона в формате +7XXXXXXXXXX")
    telegram_id: Optional[int] = Field(default=None, description="Telegram ID пользователя")
    yoga_experience: bool = Field(..., description="Есть ли опыт занятий йогой")
    intensity_preference: str = Field(..., description="Предпочтения по интенсивности")
    time_preference: str = Field(..., description="Предпочтения по времени занятий")
    created_at: datetime = Field(default_factory=datetime.now, description="Дата создания")
    status: ClientStatus = Field(default=ClientStatus.ACTIVE, description="Статус клиента")
    
    # Дополнительные поля для анкеты
    age: Optional[int] = Field(default=None, ge=16, le=100, description="Возраст клиента")
    injuries: Optional[str] = Field(default=None, max_length=500, description="Травмы и ограничения")
    goals: Optional[str] = Field(default=None, max_length=500, description="Цели от занятий")
    how_found_us: Optional[str] = Field(default=None, max_length=200, description="Как узнал о студии")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Валидация номера телефона."""
        # Убираем все пробелы и дефисы
        phone = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Проверяем формат
        if not phone.startswith('+7') and not phone.startswith('8'):
            raise ValueError('Номер телефона должен начинаться с +7 или 8')
        
        # Нормализуем к формату +7XXXXXXXXXX
        if phone.startswith('8'):
            phone = '+7' + phone[1:]
        
        # Проверяем длину и что все символы после +7 - цифры
        if len(phone) != 12:
            raise ValueError('Номер телефона должен содержать 11 цифр после +7')
        
        if not phone[2:].isdigit():
            raise ValueError('Номер телефона должен содержать только цифры после +7')
        
        return phone
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Валидация имени."""
        name = v.strip()
        if not name:
            raise ValueError('Имя не может быть пустым')
        
        # Проверяем, что в имени есть хотя бы одна буква
        if not any(c.isalpha() for c in name):
            raise ValueError('Имя должно содержать буквы')
            
        return name
    
    @field_validator('intensity_preference')
    @classmethod
    def validate_intensity(cls, v: str) -> str:
        """Валидация предпочтений по интенсивности."""
        mapping = {
            'низкая': 'низкая',
            'средняя': 'средняя',
            'высокая': 'высокая',
            'любая': 'любая'
        }
        key = v.lower()
        if key not in mapping:
            raise ValueError('Интенсивность должна быть одной из: низкая/средняя/высокая/любая')
        return mapping[key]
    
    @field_validator('time_preference')
    @classmethod
    def validate_time_preference(cls, v: str) -> str:
        """Валидация предпочтений по времени."""
        mapping = {
            'утро': 'утро',
            'день': 'день',
            'вечер': 'вечер',
            'любое': 'любое'
        }
        key = v.lower()
        if key not in mapping:
            raise ValueError('Время должно быть одним из: утро/день/вечер/любое')
        return mapping[key]

    def __str__(self) -> str:
        """Строковое представление клиента."""
        return f"Client({self.name}, {self.phone})"
    
    def __repr__(self) -> str:
        """Repr представление клиента."""
        return f"Client(id={self.id}, name={self.name}, phone={self.phone}, status={self.status})"


class ClientCreateData(BaseModel):
    """
    Данные для создания нового клиента.
    
    Используется при регистрации через Telegram бот.
    """
    
    name: str = Field(..., min_length=2, max_length=100, description="Имя клиента")
    phone: str = Field(..., description="Номер телефона")
    telegram_id: Optional[int] = Field(default=None, description="Telegram ID пользователя")
    yoga_experience: bool = Field(..., description="Есть ли опыт занятий йогой")
    intensity_preference: str = Field(..., description="Предпочтения по интенсивности")
    time_preference: str = Field(..., description="Предпочтения по времени занятий")
    
    # Опциональные поля анкеты
    age: Optional[int] = Field(default=None, ge=16, le=100, description="Возраст клиента")
    injuries: Optional[str] = Field(default=None, max_length=500, description="Травмы и ограничения")
    goals: Optional[str] = Field(default=None, max_length=500, description="Цели от занятий")
    how_found_us: Optional[str] = Field(default=None, max_length=200, description="Как узнал о студии")
    
    # Валидаторы наследуются от основной модели
    _validate_phone = field_validator('phone')(Client.validate_phone.__func__)
    _validate_name = field_validator('name')(Client.validate_name.__func__)
    _validate_intensity = field_validator('intensity_preference')(Client.validate_intensity.__func__)
    _validate_time_preference = field_validator('time_preference')(Client.validate_time_preference.__func__)


class ClientUpdateData(BaseModel):
    """
    Данные для обновления существующего клиента.
    
    Все поля опциональные - обновляются только переданные.
    """
    
    name: Optional[str] = Field(default=None, min_length=2, max_length=100, description="Имя клиента")
    phone: Optional[str] = Field(default=None, description="Номер телефона")
    yoga_experience: Optional[bool] = Field(default=None, description="Есть ли опыт занятий йогой")
    intensity_preference: Optional[str] = Field(default=None, description="Предпочтения по интенсивности")
    time_preference: Optional[str] = Field(default=None, description="Предпочтения по времени занятий")
    status: Optional[ClientStatus] = Field(default=None, description="Статус клиента")
    
    # Опциональные поля анкеты
    age: Optional[int] = Field(default=None, ge=16, le=100, description="Возраст клиента")
    injuries: Optional[str] = Field(default=None, max_length=500, description="Травмы и ограничения")
    goals: Optional[str] = Field(default=None, max_length=500, description="Цели от занятий")
    how_found_us: Optional[str] = Field(default=None, max_length=200, description="Как узнал о студии")
    
    # Валидаторы наследуются от основной модели (только для заданных полей)
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return Client.validate_phone(v)
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return Client.validate_name(v)
        return v
    
    @field_validator('intensity_preference')
    @classmethod
    def validate_intensity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return Client.validate_intensity(v)
        return v
    
    @field_validator('time_preference')
    @classmethod
    def validate_time_preference(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return Client.validate_time_preference(v)
        return v 