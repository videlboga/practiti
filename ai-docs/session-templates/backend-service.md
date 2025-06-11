# 🎯 ШАБЛОН ИИ-СЕССИИ: BACKEND SERVICE

## 📋 ПОДГОТОВКА К СЕССИИ

### 1. ПРОЧИТАТЬ ОБЯЗАТЕЛЬНО:
- `/ARCHITECTURE.md` - раздел "Сервисные интерфейсы"
- `/ai-docs/rules.md` - архитектурные ограничения
- Контракты моделей из `/shared/types/`

### 2. ОПРЕДЕЛИТЬ СЕРВИС:
- Какую бизнес-логику реализуем?
- С какими моделями работаем?
- Какие репозитории нужны?

---

## 🏗️ СТРУКТУРА СЕССИИ

### ШАГ 1: Создать протокол сервиса
```python
# Файл: backend/src/services/protocols/{service_name}_protocol.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.{model} import {Model}, {ModelCreateData}, {ModelUpdateData}

class {ServiceName}Protocol(ABC):
    @abstractmethod
    async def create_{entity}(self, data: {ModelCreateData}) -> {Model}:
        """Создает новый {entity}."""
        pass
    
    @abstractmethod
    async def get_{entity}(self, {entity}_id: str) -> Optional[{Model}]:
        """Получает {entity} по ID."""
        pass
    
    @abstractmethod
    async def search_{entities}(self, query: str) -> List[{Model}]:
        """Поиск {entities} по запросу."""
        pass
    
    @abstractmethod
    async def update_{entity}(self, {entity}_id: str, data: {ModelUpdateData}) -> {Model}:
        """Обновляет {entity}."""
        pass
    
    @abstractmethod
    async def delete_{entity}(self, {entity}_id: str) -> bool:
        """Удаляет {entity}."""
        pass
```

### ШАГ 2: Реализовать сервис
```python
# Файл: backend/src/services/{service_name}_service.py
from typing import List, Optional
from .protocols.{service_name}_protocol import {ServiceName}Protocol
from ..repositories.protocols.{repository_name}_protocol import {RepositoryName}Protocol
from ..models.{model} import {Model}, {ModelCreateData}, {ModelUpdateData}
from ..utils.logger import get_logger
from ..utils.exceptions import ValidationError, BusinessLogicError

logger = get_logger(__name__)

class {ServiceName}({ServiceName}Protocol):
    """Сервис для работы с {entities}."""
    
    def __init__(self, repository: {RepositoryName}Protocol):
        self.repository = repository
    
    async def create_{entity}(self, data: {ModelCreateData}) -> {Model}:
        """Создает нового {entity} после валидации."""
        logger.info(f"Creating {entity}: {data}")
        
        try:
            # Валидация бизнес-правил
            await self._validate_{entity}_data(data)
            
            # Проверка уникальности (если нужно)
            existing = await self.repository.get_{entity}_by_field(data.unique_field)
            if existing:
                raise BusinessLogicError(f"{Entity} with this field already exists")
            
            # Создание
            {entity} = await self.repository.save_{entity}(data)
            
            logger.info(f"{Entity} created successfully: {{{entity}.id}}")
            return {entity}
            
        except ValidationError as e:
            logger.error(f"Validation failed for {entity}: {e}")
            raise
        except BusinessLogicError as e:
            logger.error(f"Business logic error: {e}")
            raise
        except Exception as e:
            logger.critical(f"Unexpected error creating {entity}: {e}")
            raise IntegrationError(f"Failed to create {entity}")
    
    async def get_{entity}(self, {entity}_id: str) -> Optional[{Model}]:
        """Получает {entity} по ID."""
        logger.debug(f"Getting {entity}: {{{entity}_id}}")
        
        try:
            {entity} = await self.repository.get_{entity}({entity}_id)
            if not {entity}:
                logger.warning(f"{Entity} not found: {{{entity}_id}}")
            return {entity}
            
        except Exception as e:
            logger.error(f"Error getting {entity}: {e}")
            raise IntegrationError(f"Failed to get {entity}")
    
    async def search_{entities}(self, query: str) -> List[{Model}]:
        """Поиск {entities} по запросу."""
        logger.info(f"Searching {entities}: {{query}}")
        
        try:
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query too short")
            
            results = await self.repository.search_{entities}(query.strip())
            logger.info(f"Found {{len(results)}} {entities}")
            return results
            
        except ValidationError as e:
            logger.error(f"Search validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching {entities}: {e}")
            raise IntegrationError(f"Failed to search {entities}")
    
    async def update_{entity}(self, {entity}_id: str, data: {ModelUpdateData}) -> {Model}:
        """Обновляет {entity}."""
        logger.info(f"Updating {entity}: {{{entity}_id}}")
        
        try:
            # Проверяем существование
            existing = await self.get_{entity}({entity}_id)
            if not existing:
                raise BusinessLogicError(f"{Entity} not found")
            
            # Валидация изменений
            await self._validate_{entity}_update(existing, data)
            
            # Обновление
            updated_{entity} = await self.repository.update_{entity}({entity}_id, data)
            
            logger.info(f"{Entity} updated successfully: {{{entity}_id}}")
            return updated_{entity}
            
        except BusinessLogicError as e:
            logger.error(f"Business logic error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating {entity}: {e}")
            raise IntegrationError(f"Failed to update {entity}")
    
    async def delete_{entity}(self, {entity}_id: str) -> bool:
        """Удаляет {entity}."""
        logger.info(f"Deleting {entity}: {{{entity}_id}}")
        
        try:
            # Проверяем возможность удаления
            await self._validate_{entity}_deletion({entity}_id)
            
            # Удаление
            result = await self.repository.delete_{entity}({entity}_id)
            
            if result:
                logger.info(f"{Entity} deleted successfully: {{{entity}_id}}")
            else:
                logger.warning(f"Failed to delete {entity}: {{{entity}_id}}")
            
            return result
            
        except BusinessLogicError as e:
            logger.error(f"Cannot delete {entity}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting {entity}: {e}")
            raise IntegrationError(f"Failed to delete {entity}")
    
    async def _validate_{entity}_data(self, data: {ModelCreateData}) -> None:
        """Валидация данных {entity}."""
        # Реализовать специфичную валидацию
        pass
    
    async def _validate_{entity}_update(self, existing: {Model}, data: {ModelUpdateData}) -> None:
        """Валидация обновления {entity}."""
        # Реализовать валидацию изменений
        pass
    
    async def _validate_{entity}_deletion(self, {entity}_id: str) -> None:
        """Валидация возможности удаления {entity}."""
        # Проверить связанные записи, бизнес-правила
        pass
```

### ШАГ 3: Создать тесты
```python
# Файл: backend/tests/unit/services/test_{service_name}_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.services.{service_name}_service import {ServiceName}
from src.models.{model} import {Model}, {ModelCreateData}, {ModelUpdateData}
from src.utils.exceptions import ValidationError, BusinessLogicError

class Test{ServiceName}:
    def setup_method(self):
        self.mock_repository = Mock()
        self.service = {ServiceName}(self.mock_repository)
    
    @pytest.mark.asyncio
    async def test_create_{entity}_success(self):
        # Arrange
        create_data = {ModelCreateData}(
            # заполнить тестовыми данными
        )
        expected_{entity} = {Model}(id="test-id", **create_data.__dict__)
        self.mock_repository.get_{entity}_by_field = AsyncMock(return_value=None)
        self.mock_repository.save_{entity} = AsyncMock(return_value=expected_{entity})
        
        # Act
        result = await self.service.create_{entity}(create_data)
        
        # Assert
        assert result.id == expected_{entity}.id
        self.mock_repository.save_{entity}.assert_called_once_with(create_data)
    
    @pytest.mark.asyncio
    async def test_create_{entity}_validation_error(self):
        # Arrange
        invalid_data = {ModelCreateData}(
            # невалидные данные
        )
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await self.service.create_{entity}(invalid_data)
    
    @pytest.mark.asyncio
    async def test_get_{entity}_success(self):
        # Arrange
        {entity}_id = "test-id"
        expected_{entity} = {Model}(id={entity}_id)
        self.mock_repository.get_{entity} = AsyncMock(return_value=expected_{entity})
        
        # Act
        result = await self.service.get_{entity}({entity}_id)
        
        # Assert
        assert result == expected_{entity}
        self.mock_repository.get_{entity}.assert_called_once_with({entity}_id)
    
    @pytest.mark.asyncio
    async def test_get_{entity}_not_found(self):
        # Arrange
        {entity}_id = "nonexistent-id"
        self.mock_repository.get_{entity} = AsyncMock(return_value=None)
        
        # Act
        result = await self.service.get_{entity}({entity}_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_search_{entities}_success(self):
        # Arrange
        query = "test query"
        expected_results = [{Model}(id="1"), {Model}(id="2")]
        self.mock_repository.search_{entities} = AsyncMock(return_value=expected_results)
        
        # Act
        results = await self.service.search_{entities}(query)
        
        # Assert
        assert len(results) == 2
        self.mock_repository.search_{entities}.assert_called_once_with(query)
    
    @pytest.mark.asyncio
    async def test_search_{entities}_short_query(self):
        # Arrange
        short_query = "a"
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await self.service.search_{entities}(short_query)
```

### ШАГ 4: Создать фабрику сервисов
```python
# Файл: backend/src/services/factory.py
from .{service_name}_service import {ServiceName}
from ..repositories.factory import RepositoryFactory

class ServiceFactory:
    def __init__(self, repo_factory: RepositoryFactory):
        self.repo_factory = repo_factory
    
    def create_{service_name}_service(self) -> {ServiceName}:
        """Создает сервис {service_name}."""
        repository = self.repo_factory.create_{repository_name}_repository()
        return {ServiceName}(repository)
```

---

## ✅ ЧЕКЛИСТ ЗАВЕРШЕНИЯ СЕССИИ

- [ ] Протокол сервиса создан с полным интерфейсом
- [ ] Реализация сервиса соответствует протоколу
- [ ] Все методы имеют docstrings
- [ ] Валидация данных реализована
- [ ] Обработка ошибок настроена
- [ ] Логирование добавлено во все методы
- [ ] Unit тесты покрывают основные сценарии
- [ ] Тесты на ошибки написаны
- [ ] Фабрика сервисов обновлена
- [ ] Сервис зарегистрирован в DI контейнере

---

## 🚨 ФИНАЛЬНАЯ ПРОВЕРКА

Перед коммитом убедиться:
1. Сервис не импортирует репозитории напрямую
2. Вся логика инкапсулирована в сервисе
3. Нет прямых обращений к внешним API
4. Исключения правильно типизированы
5. Все async методы await-ятся

**Коммит только после 100% готовности!** 