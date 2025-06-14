# 🤖 CURSOR RULES - BACKEND DEVELOPER

## 🚨 КРИТИЧЕСКИ ВАЖНО!

**Эти правила ОБЯЗАТЕЛЬНЫ при каждой ИИ-сессии. Нарушение = провал сессии!**

---

## 📋 ПЕРЕД НАЧАЛОМ СЕССИИ

### 1. ОБЯЗАТЕЛЬНОЕ ЧТЕНИЕ:
- `/dev1-backend/architecture.md` - backend архитектура
- `/dev1-backend/session-plan.md` - план текущей сессии
- Соответствующий шаблон из `/dev1-backend/templates/`

### 2. ПРОВЕРИТЬ КОНТЕКСТ:
- Какой слой архитектуры затрагиваем?
- Какие модели и сервисы используем?
- Есть ли зависимости от других компонентов?

---

## 🏗️ АРХИТЕКТУРНЫЕ ПРИНЦИПЫ

### СЛОЕВАЯ АРХИТЕКТУРА - СТРОГО!
```
┌─────────────────┐
│  TELEGRAM BOT   │ ← Презентационный слой
├─────────────────┤
│   REST API      │ ← API слой
├─────────────────┤
│   SERVICES      │ ← Бизнес-логика
├─────────────────┤
│  REPOSITORIES   │ ← Доступ к данным
├─────────────────┤
│ GOOGLE SHEETS   │ ← Хранилище
└─────────────────┘
```

### 🚫 ЗАПРЕЩЕНО:
- Прямые импорты между несоседними слоями
- Бизнес-логика в handlers/controllers
- Прямые обращения к Google Sheets из сервисов
- Глобальные переменные
- Синглтоны (кроме config)

### ✅ ОБЯЗАТЕЛЬНО:
- Dependency Injection через конструктор
- Протоколы (ABC) для всех интерфейсов
- Async/await для всех I/O операций
- Type hints для всех методов
- Валидация входных данных

---

## 📝 ОБЯЗАТЕЛЬНЫЕ ШАБЛОНЫ

### Backend Service Pattern:
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.client import Client, ClientCreateData
from ..repositories.protocols.client_repository import ClientRepositoryProtocol
from ..utils.logger import get_logger
from ..utils.exceptions import ValidationError, BusinessLogicError

logger = get_logger(__name__)

class ClientServiceProtocol(ABC):
    @abstractmethod
    async def create_client(self, data: ClientCreateData) -> Client: ...

class ClientService(ClientServiceProtocol):
    def __init__(self, repository: ClientRepositoryProtocol):
        self.repository = repository
    
    async def create_client(self, data: ClientCreateData) -> Client:
        """Создает нового клиента после валидации."""
        logger.info(f"Creating client: {data.phone}")
        
        try:
            # Валидация
            self._validate_client_data(data)
            
            # Бизнес-логика
            client = await self.repository.save_client(data)
            
            logger.info(f"Client created: {client.id}")
            return client
            
        except ValidationError as e:
            logger.error(f"Validation failed: {e}")
            raise
        except Exception as e:
            logger.critical(f"Unexpected error: {e}")
            raise IntegrationError("Failed to create client")
```

### Repository Pattern:
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.client import Client, ClientCreateData

class ClientRepositoryProtocol(ABC):
    @abstractmethod
    async def save_client(self, data: ClientCreateData) -> Client: ...
    
    @abstractmethod
    async def get_client_by_phone(self, phone: str) -> Optional[Client]: ...

class GoogleSheetsClientRepository(ClientRepositoryProtocol):
    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets_client = sheets_client
    
    async def save_client(self, data: ClientCreateData) -> Client:
        # Реализация сохранения в Google Sheets
        pass
```

### Telegram Handler Pattern:
```python
from telegram import Update
from telegram.ext import ContextTypes
from ..services.protocols.client_service import ClientServiceProtocol
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ClientRegistrationHandler:
    def __init__(self, client_service: ClientServiceProtocol):
        self.client_service = client_service
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработчик команды /start."""
        user = update.effective_user
        logger.info(f"User started registration: {user.id}")
        
        try:
            # Логика обработки
            await update.message.reply_text("Добро пожаловать! Как вас зовут?")
            return WAITING_NAME
            
        except Exception as e:
            logger.error(f"Error in start handler: {e}")
            await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
            return ConversationHandler.END
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit Test Pattern:
```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.services.client_service import ClientService
from src.models.client import ClientCreateData, Client

class TestClientService:
    def setup_method(self):
        self.mock_repository = Mock()
        self.service = ClientService(self.mock_repository)
    
    @pytest.mark.asyncio
    async def test_create_client_success(self):
        # Arrange
        client_data = ClientCreateData(name="Test", phone="+79991234567")
        expected_client = Client(id="123", **client_data.__dict__)
        self.mock_repository.save_client = AsyncMock(return_value=expected_client)
        
        # Act
        result = await self.service.create_client(client_data)
        
        # Assert
        assert result.name == client_data.name
        self.mock_repository.save_client.assert_called_once_with(client_data)
```

### Integration Test Pattern:
```python
import pytest
from src.integrations.google_sheets import GoogleSheetsClient
from src.repositories.client_repository import GoogleSheetsClientRepository

@pytest.mark.integration
class TestGoogleSheetsIntegration:
    @pytest.fixture
    def repository(self):
        sheets_client = GoogleSheetsClient(test_config)
        return GoogleSheetsClientRepository(sheets_client)
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_client(self, repository):
        # Тест реальной интеграции с Google Sheets
        pass
```

---

## 🔧 КОНФИГУРАЦИЯ

### Environment Variables Pattern:
```python
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str
    telegram_admin_chat_id: int
    
    # Google Sheets
    google_sheets_id: str
    google_credentials_path: str
    
    # API
    api_host: str = "localhost"
    api_port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 📊 ЛОГИРОВАНИЕ

### Обязательный формат:
```python
import logging
from typing import Any, Dict

def get_logger(name: str) -> logging.Logger:
    """Создает настроенный логгер."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Настройка форматирования
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )
    
    return logger

# Использование
logger = get_logger(__name__)

# Логирование операций
logger.info(f"Starting operation: {operation_name}", extra={
    "user_id": user_id,
    "operation": operation_name
})
```

### Что логировать:
- Начало/конец всех async операций
- Входные параметры (без sensitive данных)
- Ошибки с полным traceback
- Интеграции с внешними API
- Пользовательские действия в боте

---

## 🛡️ ОБРАБОТКА ОШИБОК

### Иерархия исключений:
```python
class PrakritiException(Exception):
    """Базовое исключение приложения."""
    pass

class ValidationError(PrakritiException):
    """Ошибка валидации данных."""
    pass

class BusinessLogicError(PrakritiException):
    """Нарушение бизнес-правил."""
    pass

class IntegrationError(PrakritiException):
    """Ошибка интеграции с внешними сервисами."""
    pass
```

### Паттерн обработки:
```python
try:
    result = await service.do_something()
    return result
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise  # Пробрасываем validation ошибки
except BusinessLogicError as e:
    logger.error(f"Business logic error: {e}")
    raise  # Пробрасываем business ошибки
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    raise IntegrationError("Operation failed")
```

---

## 🎯 TELEGRAM BOT СПЕЦИФИКА

### State Machine Pattern:
```python
from enum import Enum
from telegram.ext import ConversationHandler

class RegistrationState(Enum):
    WAITING_NAME = "waiting_name"
    WAITING_PHONE = "waiting_phone"
    WAITING_EXPERIENCE = "waiting_experience"
    WAITING_INTENSITY = "waiting_intensity"
    WAITING_TIME = "waiting_time"

# Использование в handlers
async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user_name = update.message.text
    context.user_data['name'] = user_name
    
    await update.message.reply_text("Отлично! Теперь введите ваш номер телефона:")
    return RegistrationState.WAITING_PHONE.value
```

### Keyboard Pattern:
```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def create_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру Да/Нет."""
    keyboard = [
        [
            InlineKeyboardButton("Да", callback_data="yes"),
            InlineKeyboardButton("Нет", callback_data="no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
```

---

## 📅 ПЛАНИРОВЩИК ЗАДАЧ

### APScheduler Pattern:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta

class ReminderScheduler:
    def __init__(self, notification_service: NotificationServiceProtocol):
        self.notification_service = notification_service
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Запускает планировщик."""
        self.scheduler.start()
    
    async def schedule_class_reminder(self, client_id: str, class_datetime: datetime):
        """Планирует напоминание о занятии."""
        reminder_time = class_datetime - timedelta(hours=2)
        
        self.scheduler.add_job(
            self._send_class_reminder,
            trigger='date',
            run_date=reminder_time,
            args=[client_id, class_datetime],
            id=f"reminder_{client_id}_{class_datetime.isoformat()}"
        )
```

---

## ✅ ЧЕКЛИСТ ЗАВЕРШЕНИЯ СЕССИИ

### Обязательно проверить:
- [ ] Все методы имеют type hints
- [ ] Все async методы используют await
- [ ] Логирование добавлено во все публичные методы
- [ ] Обработка ошибок реализована
- [ ] Unit тесты покрывают основные сценарии
- [ ] Нет прямых импортов между слоями
- [ ] Конфигурация не хардкодится
- [ ] Валидация входных данных есть

### Финальные команды:
```bash
# Форматирование
black src/
isort src/

# Проверки
mypy src/
flake8 src/
pytest tests/ -v

# Только после успешных проверок - коммит!
git add .
git commit -m "feat(backend): описание фичи"
```

---

## 🚫 КРАСНЫЕ ФЛАГИ

**СТОП! НЕ КОММИТЬ, если:**
- ❌ Есть TODO/FIXME комментарии
- ❌ Тесты падают
- ❌ Mypy выдает ошибки
- ❌ Есть print() отладка
- ❌ Хардкод токенов/паролей
- ❌ Нет обработки исключений
- ❌ Отсутствуют type hints

---

**ПОМНИ: Простота превыше всего! Каждая строка кода должна быть понятна и необходима.** 