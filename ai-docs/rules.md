# 🤖 ПРАВИЛА ДЛЯ ИИ-АССИСТЕНТОВ ПРОЕКТА "ПРАКРИТИ"

## 🚨 КРИТИЧЕСКИ ВАЖНО!

**Эти правила ОБЯЗАТЕЛЬНЫ для выполнения. Нарушение = провал ИИ-сессии!**

---

## 📋 ПЕРЕД НАЧАЛОМ КАЖДОЙ СЕССИИ

### 1. ПРОЧИТАТЬ ОБЯЗАТЕЛЬНО:
- `/ARCHITECTURE.md` - основная архитектура
- `/ai-docs/rules.md` - этот файл
- Соответствующий шаблон из `/ai-docs/session-templates/`

### 2. ПРОВЕРИТЬ КОНТЕКСТ:
- В какой части архитектуры работаем?
- Какие контракты затрагиваем?
- Есть ли зависимости от других модулей?

### 3. ПОДТВЕРДИТЬ ПЛАН:
- Описать что будем делать
- Указать затрагиваемые файлы
- Убедиться в соблюдении архитектуры

---

## 🎯 АТОМАРНОСТЬ СЕССИЙ

### ОДНА СЕССИЯ = ОДНА ФИЧА
✅ **Хорошо:**
- "Создать ClientService с методами CRUD"
- "Добавить валидацию телефона в анкету бота"
- "Реализовать компонент поиска клиентов"

❌ **Плохо:**
- "Сделать бота и админку"
- "Настроить базу данных и API"
- "Исправить все баги"

### ФИЧА ДОЛЖНА БЫТЬ ЗАВЕРШЕННОЙ:
- Основной код
- Тесты
- Документация (docstrings)
- Обработка ошибок
- Логирование

---

## 🏗️ АРХИТЕКТУРНЫЕ ОГРАНИЧЕНИЯ

### 🚫 ЗАПРЕЩЕНО СОЗДАВАТЬ:

#### Backend:
- Прямые импорты между слоями (только соседние!)
- Глобальные переменные
- Синглтоны (кроме конфига)
- Monkey patching
- Динамические импорты

#### Frontend:
- Прямые API вызовы в компонентах
- Глобальное состояние (кроме Context)
- Inline стили
- Magic strings для URL/paths
- Компоненты >300 строк

### ✅ ОБЯЗАТЕЛЬНО:

#### Backend:
```python
# ✅ Правильно - через сервисный слой
class TelegramHandler:
    def __init__(self, client_service: ClientService):
        self.client_service = client_service

# ❌ Неправильно - прямой импорт репозитория
from repositories.google_sheets import GoogleSheetsRepo
```

#### Frontend:
```typescript
// ✅ Правильно - типизированные props
interface ClientCardProps {
  client: Client;
  onEdit: (id: string) => void;
}

// ❌ Неправильно - any типы
const ClientCard = (props: any) => { ... }
```

---

## 📝 ОБЯЗАТЕЛЬНЫЕ ШАБЛОНЫ КОДА

### Backend Service:
```python
from abc import ABC, abstractmethod
from typing import Optional, List
from ..models.client import Client, ClientCreateData
from ..utils.logger import get_logger

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
            
            # Создание
            client = await self.repository.save_client(data)
            
            logger.info(f"Client created: {client.id}")
            return client
            
        except ValidationError as e:
            logger.error(f"Validation failed: {e}")
            raise
        except Exception as e:
            logger.critical(f"Unexpected error creating client: {e}")
            raise IntegrationError("Failed to create client")
    
    def _validate_client_data(self, data: ClientCreateData) -> None:
        """Валидация данных клиента."""
        if not data.phone or len(data.phone) < 10:
            raise ValidationError("Invalid phone number")
```

### Frontend Component:
```typescript
import React from 'react';
import { Client } from '../../types/client';
import { useClientActions } from '../../hooks/useClientActions';
import './ClientCard.styles.css';

interface ClientCardProps {
  client: Client;
  onEdit?: (clientId: string) => void;
  onDelete?: (clientId: string) => void;
}

export const ClientCard: React.FC<ClientCardProps> = ({
  client,
  onEdit,
  onDelete,
}) => {
  const { deleteClient, isLoading } = useClientActions();

  const handleDelete = async () => {
    if (window.confirm('Удалить клиента?')) {
      await deleteClient(client.id);
      onDelete?.(client.id);
    }
  };

  return (
    <div className="client-card" data-testid="client-card">
      <h3>{client.name}</h3>
      <p>{client.phone}</p>
      {/* Остальной JSX */}
    </div>
  );
};
```

---

## 🧪 ОБЯЗАТЕЛЬНОЕ ТЕСТИРОВАНИЕ

### Backend тест:
```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.services.client_service import ClientService
from src.models.client import ClientCreateData, Client

class TestClientService:
    def setup_method(self):
        self.mock_repo = Mock()
        self.service = ClientService(self.mock_repo)
    
    async def test_create_client_success(self):
        # Arrange
        client_data = ClientCreateData(
            name="Тест Клиент",
            phone="+79991234567"
        )
        expected_client = Client(id="123", **client_data.__dict__)
        self.mock_repo.save_client = AsyncMock(return_value=expected_client)
        
        # Act
        result = await self.service.create_client(client_data)
        
        # Assert
        assert result.name == client_data.name
        assert result.phone == client_data.phone
        self.mock_repo.save_client.assert_called_once_with(client_data)
```

### Frontend тест:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ClientCard } from './ClientCard';
import { mockClient } from '../../test-utils/mocks';

describe('ClientCard', () => {
  it('отображает информацию о клиенте', () => {
    render(<ClientCard client={mockClient} />);
    
    expect(screen.getByText(mockClient.name)).toBeInTheDocument();
    expect(screen.getByText(mockClient.phone)).toBeInTheDocument();
  });

  it('вызывает onEdit при клике на кнопку редактирования', () => {
    const mockOnEdit = jest.fn();
    render(<ClientCard client={mockClient} onEdit={mockOnEdit} />);
    
    fireEvent.click(screen.getByTestId('edit-button'));
    
    expect(mockOnEdit).toHaveBeenCalledWith(mockClient.id);
  });
});
```

---

## 📊 ЛОГИРОВАНИЕ

### Обязательные события для логирования:
- Начало/конец операций
- Ошибки валидации  
- Внешние API вызовы
- Изменения данных
- Пользовательские действия

### Формат:
```python
logger.info(f"Starting operation: {operation_name}", extra={
    "user_id": user_id,
    "operation": operation_name,
    "params": sanitized_params
})
```

---

## 🔧 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ

### Обязательная проверка:
```python
import os

def get_required_env(key: str) -> str:
    """Получает обязательную переменную окружения."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Required environment variable {key} not set")
    return value

# Использование
TELEGRAM_BOT_TOKEN = get_required_env("TELEGRAM_BOT_TOKEN")
```

---

## 🎨 СТИЛИЗАЦИЯ И UI

### CSS Modules или Styled Components:
```typescript
// ✅ Правильно
import styles from './ClientCard.module.css';

// ❌ Неправильно  
<div style={{color: 'red', margin: '10px'}}>
```

### Responsive Design:
- Mobile First подход
- Breakpoints: 320px, 768px, 1024px, 1440px
- Flexbox/Grid для layouts

---

## 🚨 СИСТЕМА ПРОВЕРОК

### Перед коммитом ОБЯЗАТЕЛЬНО:
1. ✅ Код соответствует архитектуре
2. ✅ Тесты написаны и проходят
3. ✅ Нет ESLint/PyLint ошибок
4. ✅ Docstrings добавлены
5. ✅ Логирование настроено
6. ✅ Обработка ошибок реализована

### Автоматические проверки:
```bash
# Backend
black src/
flake8 src/
mypy src/
pytest tests/

# Frontend  
npm run lint
npm run type-check
npm run test
npm run build
```

---

## 🎯 ЧЕКЛИСТ ЗАВЕРШЕНИЯ СЕССИИ

### ✅ Перед завершением проверить:
- [ ] Фича полностью реализована
- [ ] Тесты написаны и проходят
- [ ] Документация обновлена
- [ ] Нет нарушений архитектуры
- [ ] Логирование настроено
- [ ] Обработка ошибок есть
- [ ] Код отформатирован
- [ ] Переменные окружения документированы

### ✅ Финальный коммит:
```bash
git add .
git commit -m "feat(module): краткое описание фичи

- Детальное описание изменений
- Добавленные тесты
- Обновленная документация"
```

---

## 🚫 КРАСНЫЕ ФЛАГИ

**СТОП! НЕ КОММИТЬ, если:**
- ❌ Есть TODO/FIXME комментарии
- ❌ Тесты не проходят
- ❌ Есть console.log/print отладка
- ❌ Хардкод значения
- ❌ Отсутствует обработка ошибок
- ❌ Нет типизации
- ❌ Нарушена архитектура

---

**ПОМНИ: Лучше сделать маленькую фичу идеально, чем большую криво!** 