# 🏗️ АРХИТЕКТУРА TELEGRAM-БОТА "ПРАКРИТИ" ДЛЯ ИИ-РАЗРАБОТКИ

## 🤖 ПРИНЦИПЫ АГЕНТНОЙ РАЗРАБОТКИ

### Генеративная разработка = БЫСТРО + НЕПРЕДСКАЗУЕМО
**Проблема:** ИИ может сгенерировать рабочий код, но нарушить архитектуру
**Решение:** Жесткие правила и шаблоны ДО начала кодинга

---

## 📋 КУРСОР-РУЛС (ПРАВИЛА ДЛЯ ИИ-АССИСТЕНТОВ)

### 🎯 ОБЩИЕ ПРИНЦИПЫ

1. **АТОМАРНОСТЬ СЕССИЙ** - каждая ИИ-сессия = одна завершенная фича
2. **ПРЕДСКАЗУЕМОСТЬ** - строго следовать архитектурным шаблонам
3. **ИЗОЛЯЦИЯ** - модули не зависят друг от друга
4. **КОНТРАКТНОСТЬ** - четкие API контракты между модулями
5. **ТЕСТИРУЕМОСТЬ** - каждый модуль покрыт тестами

### 🚫 ЗАПРЕТЫ ДЛЯ ИИ

❌ **НЕ СОЗДАВАТЬ:**
- Новые архитектурные паттерны
- Кроссмодульные зависимости
- Глобальные переменные
- Сложные inheritance цепочки
- Magic numbers/strings

❌ **НЕ ИЗМЕНЯТЬ:**
- Структуру папок
- Интерфейсы между модулями
- Схемы данных без согласования
- Конфигурационные файлы

### ✅ ОБЯЗАТЕЛЬНО ДЕЛАТЬ

✅ **ВСЕГДА:**
- Использовать готовые шаблоны
- Добавлять type hints
- Писать docstrings
- Валидировать входные данные
- Обрабатывать ошибки
- Логировать действия

---

## 🏛️ АРХИТЕКТУРНЫЕ СЛОИ

```
┌─────────────────┐
│   TELEGRAM BOT  │ ← Презентационный слой
├─────────────────┤
│    WEB ADMIN    │ ← Презентационный слой  
├─────────────────┤
│   API GATEWAY   │ ← Маршрутизация
├─────────────────┤
│   SERVICES      │ ← Бизнес-логика
├─────────────────┤
│   REPOSITORIES  │ ← Доступ к данным
├─────────────────┤
│  GOOGLE SHEETS  │ ← Хранилище данных
└─────────────────┘
```

### ПРИНЦИП: Каждый слой общается только с соседним!

---

## 📁 ЖЕЛЕЗНАЯ СТРУКТУРА ПРОЕКТА

```
practiti/
├── 🤖 ai-docs/                 # Документация для ИИ
│   ├── session-templates/      # Шаблоны для ИИ-сессий
│   ├── code-patterns/          # Паттерны кода
│   └── rules.md               # Правила для ИИ
├── 🔧 backend/
│   ├── src/
│   │   ├── 🎭 presentation/   # Telegram Bot handlers
│   │   ├── 🌐 api/            # REST API endpoints
│   │   ├── 💼 services/       # Бизнес-логика
│   │   ├── 🗄️ repositories/   # Доступ к данным
│   │   ├── 📊 models/         # Модели данных
│   │   ├── 🔌 integrations/   # Внешние API
│   │   └── 🛠️ utils/          # Утилиты
│   ├── tests/                 # Тесты
│   └── config/                # Конфигурация
├── 🎨 frontend/
│   ├── src/
│   │   ├── 📄 pages/          # Страницы
│   │   ├── 🧩 components/     # Компоненты
│   │   ├── 🔗 services/       # API клиенты
│   │   ├── 🎨 styles/         # Стили
│   │   └── 📝 types/          # TypeScript типы
├── 📚 shared/                 # Общие типы и константы
└── 🐳 docker/                 # Docker конфигурация
```

### 🔒 ПРАВИЛО: Структура НЕИЗМЕННА!

---

## 🎯 КОНТРАКТЫ МЕЖДУ МОДУЛЯМИ

### 📋 1. CLIENT CONTRACT (Клиент)
```python
@dataclass
class Client:
    id: str
    name: str
    phone: str
    telegram_id: int
    yoga_experience: bool
    intensity_preference: str
    time_preference: str
    created_at: datetime
    status: ClientStatus
```

### 🎫 2. SUBSCRIPTION CONTRACT (Абонемент)
```python
@dataclass
class Subscription:
    id: str
    client_id: str
    type: SubscriptionType
    total_classes: int
    used_classes: int
    remaining_classes: int
    start_date: date
    end_date: date
    status: SubscriptionStatus
```

### 📅 3. BOOKING CONTRACT (Запись)
```python
@dataclass
class Booking:
    id: str
    client_id: str
    class_date: datetime
    class_type: str
    status: BookingStatus
    created_at: datetime
```

### 🔒 ПРАВИЛО: Контракты НЕИЗМЕННЫ без обсуждения!

---

## 🎭 СЕРВИСНЫЕ ИНТЕРФЕЙСЫ

### ClientService
```python
class ClientService:
    async def create_client(self, data: ClientCreateData) -> Client
    async def get_client(self, client_id: str) -> Client
    async def search_clients(self, query: str) -> List[Client]
    async def update_client(self, client_id: str, data: ClientUpdateData) -> Client
```

### SubscriptionService  
```python
class SubscriptionService:
    async def create_subscription(self, data: SubscriptionCreateData) -> Subscription
    async def confirm_payment(self, subscription_id: str) -> Subscription
    async def use_class(self, subscription_id: str) -> Subscription
    async def extend_subscription(self, subscription_id: str, days: int) -> Subscription
```

### NotificationService
```python
class NotificationService:
    async def send_reminder(self, client_id: str, message: str) -> bool
    async def send_admin_notification(self, message: str) -> bool
    async def schedule_reminder(self, client_id: str, when: datetime, message: str) -> bool
```

---

## 🎨 FRONTEND АРХИТЕКТУРА

### Структура компонентов:
```
components/
├── common/           # Переиспользуемые компоненты
├── client/          # Компоненты для работы с клиентами
├── subscription/    # Компоненты абонементов
├── booking/         # Компоненты записей
└── layout/          # Layout компоненты
```

### Правила компонентов:
1. **Один компонент = одна ответственность**
2. **Props типизированы через interface**
3. **Состояние только локальное или через Context**
4. **API вызовы только через хуки**

---

## 🔄 ПАТТЕРНЫ ИНТЕГРАЦИИ

### Google Sheets Repository Pattern:
```python
class GoogleSheetsRepository:
    async def save_client(self, client: Client) -> bool
    async def get_client_by_phone(self, phone: str) -> Optional[Client]
    async def update_subscription(self, subscription: Subscription) -> bool
```

### Telegram Bot Handler Pattern:
```python
class BaseHandler:
    def __init__(self, service: ServiceProtocol):
        self.service = service
    
    async def handle(self, update: Update, context: Context) -> None:
        # Шаблон обработки
```

---

## 📊 СИСТЕМА ЛОГИРОВАНИЯ

### Уровни логов:
- **DEBUG** - детальная отладочная информация
- **INFO** - важные события системы
- **WARNING** - потенциальные проблемы
- **ERROR** - ошибки обработки
- **CRITICAL** - критические ошибки системы

### Формат логов:
```
[TIMESTAMP] [LEVEL] [MODULE] [USER_ID] MESSAGE
```

---

## 🛡️ ОБРАБОТКА ОШИБОК

### Иерархия исключений:
```python
class PrakritiException(Exception): pass
class ValidationError(PrakritiException): pass
class IntegrationError(PrakritiException): pass
class BusinessLogicError(PrakritiException): pass
```

### Паттерн обработки:
```python
try:
    result = await service.do_something()
except PrakritiException as e:
    logger.error(f"Business error: {e}")
    await notify_admin(f"Error: {e}")
    return error_response(e)
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    return critical_error_response()
```

---

## 🔧 КОНФИГУРАЦИЯ

### Environment Variables:
```env
# Telegram
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_ADMIN_CHAT_ID=xxx

# Google Sheets
GOOGLE_SHEETS_ID=xxx
GOOGLE_CREDENTIALS_PATH=xxx

# API
API_HOST=localhost
API_PORT=8000
```

### Конфигурационные классы:
```python
@dataclass
class TelegramConfig:
    bot_token: str
    admin_chat_id: int

@dataclass
class GoogleSheetsConfig:
    spreadsheet_id: str
    credentials_path: str
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Структура тестов:
```
tests/
├── unit/           # Unit тесты
├── integration/    # Интеграционные тесты
├── fixtures/       # Тестовые данные
└── mocks/          # Моки для внешних сервисов
```

### Паттерн тестирования:
```python
class TestClientService:
    def setup_method(self):
        self.mock_repo = Mock()
        self.service = ClientService(self.mock_repo)
    
    async def test_create_client_success(self):
        # Arrange
        client_data = ClientCreateData(...)
        # Act
        result = await self.service.create_client(client_data)
        # Assert
        assert result.name == client_data.name
```

---

## 🎯 КРИТЕРИИ ГОТОВНОСТИ МОДУЛЯ

Модуль считается готовым, если:
- ✅ Соответствует архитектуре
- ✅ Покрыт unit тестами
- ✅ Имеет docstrings
- ✅ Обрабатывает ошибки
- ✅ Логирует действия
- ✅ Валидирует данные
- ✅ Протестирован интеграционно

---

## 🚨 СИСТЕМА АЛЕРТОВ

### Когда уведомлять разработчиков:
1. Нарушение архитектурных принципов
2. Отсутствие тестов
3. Критические ошибки в логах
4. Падение интеграций
5. Превышение времени отклика

---

Эта архитектура ОБЯЗАТЕЛЬНА для соблюдения всеми ИИ-ассистентами! 