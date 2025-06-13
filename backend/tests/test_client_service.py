"""
🧪 Unit тесты для ClientService

Тестирует всю бизнес-логику сервиса работы с клиентами.
Принцип CyberKitty: мок ответ в тесте это провал теста.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from src.models.client import Client, ClientCreateData, ClientUpdateData, ClientStatus
from src.services.client_service import ClientService
from src.utils.exceptions import ValidationError, BusinessLogicError


class TestClientService:
    """Тесты ClientService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Мок репозитория для тестов."""
        repository = AsyncMock()
        return repository
    
    @pytest.fixture
    def client_service(self, mock_repository):
        """Экземпляр ClientService для тестов."""
        return ClientService(mock_repository)
    
    @pytest.fixture
    def sample_client_create_data(self):
        """Пример данных для создания клиента."""
        return ClientCreateData(
            name="Анна Петрова",
            phone="+79161234567",
            telegram_id=123456789,
            yoga_experience=True,
            intensity_preference="средняя",
            time_preference="вечер",
            age=30,
            injuries="Проблемы со спиной",
            goals="Улучшение гибкости",
            how_found_us="Рекомендация друзей"
        )
    
    @pytest.fixture
    def sample_client(self):
        """Пример клиента."""
        return Client(
            id="test-client-id",
            name="Анна Петрова",
            phone="+79161234567",
            telegram_id=123456789,
            yoga_experience=True,
            intensity_preference="средняя",
            time_preference="вечер",
            age=30,
            injuries="Проблемы со спиной",
            goals="Улучшение гибкости",
            how_found_us="Рекомендация друзей",
            status=ClientStatus.ACTIVE,
            created_at=datetime.now()
        )


class TestCreateClient(TestClientService):
    """Тесты создания клиента."""
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_create_client_success(self, client_service, mock_repository, sample_client_create_data, sample_client):
        """Тест успешного создания клиента."""
        # Arrange
        mock_repository.get_by_phone.return_value = None
        mock_repository.get_by_telegram_id.return_value = None
        mock_repository.save.return_value = sample_client
        
        # Act
        result = await client_service.create_client(sample_client_create_data)
        
        # Assert
        assert result == sample_client
        mock_repository.get_by_phone.assert_called_once_with("+79161234567")
        mock_repository.get_by_telegram_id.assert_called_once_with(123456789)
        mock_repository.save.assert_called_once()
        
        # Проверяем, что save был вызван с правильными данными
        save_call_args = mock_repository.save.call_args[0][0]
        assert save_call_args.name == "Анна Петрова"
        assert save_call_args.phone == "+79161234567"
        assert save_call_args.status == ClientStatus.ACTIVE
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_create_client_phone_exists(self, client_service, mock_repository, sample_client_create_data, sample_client):
        """Тест создания клиента с существующим телефоном."""
        # Arrange
        mock_repository.get_by_phone.return_value = sample_client
        
        # Act & Assert
        with pytest.raises(BusinessLogicError) as exc_info:
            await client_service.create_client(sample_client_create_data)
        
        assert "уже зарегистрирован" in str(exc_info.value)
        mock_repository.get_by_phone.assert_called_once()
        mock_repository.save.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_create_client_telegram_exists(self, client_service, mock_repository, sample_client_create_data, sample_client):
        """Тест создания клиента с существующим Telegram ID."""
        # Arrange
        mock_repository.get_by_phone.return_value = None
        mock_repository.get_by_telegram_id.return_value = sample_client
        
        # Act & Assert
        with pytest.raises(BusinessLogicError) as exc_info:
            await client_service.create_client(sample_client_create_data)
        
        assert "Telegram аккаунтом" in str(exc_info.value)
        mock_repository.get_by_telegram_id.assert_called_once()
        mock_repository.save.assert_not_called()


class TestGetClient(TestClientService):
    """Тесты получения клиента."""
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_client_success(self, client_service, mock_repository, sample_client):
        """Тест успешного получения клиента."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_client
        
        # Act
        result = await client_service.get_client("test-client-id")
        
        # Assert
        assert result == sample_client
        mock_repository.get_by_id.assert_called_once_with("test-client-id")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_client_not_found(self, client_service, mock_repository):
        """Тест получения несуществующего клиента."""
        # Arrange
        mock_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(BusinessLogicError) as exc_info:
            await client_service.get_client("nonexistent-id")
        
        assert "не найден" in str(exc_info.value)
        mock_repository.get_by_id.assert_called_once_with("nonexistent-id")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_client_empty_id(self, client_service, mock_repository):
        """Тест получения клиента с пустым ID."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await client_service.get_client("")
        
        assert "не может быть пустым" in str(exc_info.value)
        mock_repository.get_by_id.assert_not_called()


class TestGetClientByTelegramId(TestClientService):
    """Тесты получения клиента по Telegram ID."""
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_client_by_telegram_id_success(self, client_service, mock_repository, sample_client):
        """Тест успешного получения клиента по Telegram ID."""
        # Arrange
        mock_repository.get_by_telegram_id.return_value = sample_client
        
        # Act
        result = await client_service.get_client_by_telegram_id(123456789)
        
        # Assert
        assert result == sample_client
        mock_repository.get_by_telegram_id.assert_called_once_with(123456789)
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_client_by_telegram_id_not_found(self, client_service, mock_repository):
        """Тест получения несуществующего клиента по Telegram ID."""
        # Arrange
        mock_repository.get_by_telegram_id.return_value = None
        
        # Act
        result = await client_service.get_client_by_telegram_id(999999999)
        
        # Assert
        assert result is None
        mock_repository.get_by_telegram_id.assert_called_once_with(999999999)
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_client_by_telegram_id_invalid(self, client_service, mock_repository):
        """Тест получения клиента с некорректным Telegram ID."""
        # Act & Assert
        with pytest.raises(ValidationError):
            await client_service.get_client_by_telegram_id(0)
        
        mock_repository.get_by_telegram_id.assert_not_called()


class TestGetClientByPhone(TestClientService):
    """Тесты получения клиента по телефону."""
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_client_by_phone_success(self, client_service, mock_repository, sample_client):
        """Тест успешного получения клиента по телефону."""
        # Arrange
        mock_repository.get_by_phone.return_value = sample_client
        
        # Act
        result = await client_service.get_client_by_phone("+79161234567")
        
        # Assert
        assert result == sample_client
        mock_repository.get_by_phone.assert_called_once_with("+79161234567")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_client_by_phone_normalize(self, client_service, mock_repository, sample_client):
        """Тест нормализации телефона при поиске."""
        # Arrange
        mock_repository.get_by_phone.return_value = sample_client
        
        # Act
        result = await client_service.get_client_by_phone("8-916-123-45-67")
        
        # Assert
        assert result == sample_client
        # Проверяем, что телефон был нормализован
        mock_repository.get_by_phone.assert_called_once_with("+79161234567")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_get_client_by_phone_invalid_format(self, client_service, mock_repository):
        """Тест поиска с некорректным форматом телефона."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await client_service.get_client_by_phone("invalid-phone")
        
        assert "Некорректный формат телефона" in str(exc_info.value)
        mock_repository.get_by_phone.assert_not_called()


class TestSearchAndUpdate(TestClientService):
    """Тесты поиска и обновления."""
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_search_clients_success(self, client_service, mock_repository, sample_client):
        """Тест успешного поиска клиентов."""
        # Arrange
        mock_repository.search.return_value = [sample_client]
        
        # Act
        result = await client_service.search_clients("Анна")
        
        # Assert
        assert result == [sample_client]
        mock_repository.search.assert_called_once_with("Анна")
    
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_update_client_success(self, client_service, mock_repository, sample_client):
        """Тест успешного обновления клиента."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_client
        mock_repository.save.return_value = sample_client
        
        update_data = ClientUpdateData(name="Анна Иванова")
        
        # Act
        result = await client_service.update_client("test-client-id", update_data)
        
        # Assert
        assert result == sample_client
        mock_repository.get_by_id.assert_called_once_with("test-client-id")
        mock_repository.save.assert_called_once()


class TestClientStatusManagement(TestClientService):
    """Тесты управления статусами клиента."""
    
    @pytest.mark.asyncio
    async def test_delete_client(self, client_service, mock_repository, sample_client):
        """Тест мягкого удаления клиента."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_client
        mock_repository.save.return_value = sample_client
        
        # Act
        result = await client_service.delete_client("test-client-id")
        
        # Assert
        assert result is True
        # delete_client вызывает get_client и update_client, который тоже вызывает get_client
        assert mock_repository.get_by_id.call_count == 2
        mock_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_activate_client(self, client_service, mock_repository, sample_client):
        """Тест активации клиента."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_client
        mock_repository.save.return_value = sample_client
        
        # Act
        result = await client_service.activate_client("test-client-id")
        
        # Assert
        assert result == sample_client
        mock_repository.get_by_id.assert_called_once()
        mock_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate_client(self, client_service, mock_repository, sample_client):
        """Тест деактивации клиента."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_client
        mock_repository.save.return_value = sample_client
        
        # Act
        result = await client_service.deactivate_client("test-client-id")
        
        # Assert
        assert result == sample_client
        mock_repository.get_by_id.assert_called_once()
        mock_repository.save.assert_called_once()


class TestClientListMethods(TestClientService):
    """Тесты методов получения списков клиентов."""
    
    @pytest.mark.asyncio
    async def test_get_all_clients(self, client_service, mock_repository, sample_client):
        """Тест получения всех клиентов."""
        # Arrange
        mock_repository.get_all.return_value = [sample_client]
        
        # Act
        result = await client_service.get_all_clients()
        
        # Assert
        assert result == [sample_client]
        mock_repository.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_clients(self, client_service, mock_repository):
        """Тест получения только активных клиентов."""
        # Arrange
        active_client = Client(
            id="active-id",
            name="Активный",
            phone="+79161111111",
            telegram_id=111,
            yoga_experience=True,
            intensity_preference="низкая",
            time_preference="утро",
            status=ClientStatus.ACTIVE
        )
        
        inactive_client = Client(
            id="inactive-id",
            name="Неактивный",
            phone="+79162222222",
            telegram_id=222,
            yoga_experience=False,
            intensity_preference="средняя",
            time_preference="день",
            status=ClientStatus.INACTIVE
        )
        
        mock_repository.get_all.return_value = [active_client, inactive_client]
        
        # Act
        result = await client_service.get_active_clients()
        
        # Assert
        assert len(result) == 1
        assert result[0] == active_client
        assert result[0].status == ClientStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_get_clients_by_status(self, client_service, mock_repository):
        """Тест получения клиентов по статусу."""
        # Arrange
        trial_client = Client(
            id="trial-id",
            name="Пробный",
            phone="+79163333333",
            telegram_id=333,
            yoga_experience=True,
            intensity_preference="высокая",
            time_preference="вечер",
            status=ClientStatus.TRIAL
        )
        
        active_client = Client(
            id="active-id",
            name="Активный",
            phone="+79164444444",
            telegram_id=444,
            yoga_experience=False,
            intensity_preference="любая",
            time_preference="любое",
            status=ClientStatus.ACTIVE
        )
        
        mock_repository.get_all.return_value = [trial_client, active_client]
        
        # Act
        result = await client_service.get_clients_by_status(ClientStatus.TRIAL)
        
        # Assert
        assert len(result) == 1
        assert result[0] == trial_client
        assert result[0].status == ClientStatus.TRIAL 