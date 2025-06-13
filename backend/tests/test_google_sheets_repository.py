"""
🧪 Тесты для Google Sheets репозитория CyberKitty Practiti

Unit-тесты для GoogleSheetsClientRepository с использованием моков.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from backend.src.repositories.google_sheets_client_repository import GoogleSheetsClientRepository
from backend.src.models.client import ClientCreateData, ClientStatus
from backend.src.integrations.google_sheets import GoogleSheetsClient


class TestGoogleSheetsClientRepository:
    """Тесты для Google Sheets репозитория клиентов."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        # Создаём мок Google Sheets клиента
        self.mock_sheets_client = Mock(spec=GoogleSheetsClient)
        self.repository = GoogleSheetsClientRepository(self.mock_sheets_client)
    
    @pytest.mark.asyncio
    async def test_save_client_success(self):
        """Тест успешного сохранения клиента."""
        # Arrange
        client_data = ClientCreateData(
            name="Андрей",
            phone="+79991234567",
            telegram_id=123456,
            yoga_experience=True,
            intensity_preference="средняя",
            time_preference="утро"
        )
        
        # Мокаем методы
        self.mock_sheets_client.read_range = AsyncMock(return_value=[])
        self.mock_sheets_client.write_range = AsyncMock(return_value=True)
        self.mock_sheets_client.append_rows = AsyncMock(return_value=True)
        
        # Act
        result = await self.repository.save_client(client_data)
        
        # Assert
        assert result.name == "Андрей"
        assert result.phone == "+79991234567"
        assert result.status == ClientStatus.ACTIVE
        self.mock_sheets_client.append_rows.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_client_by_phone_found(self):
        """Тест поиска клиента по телефону - найден."""
        # Arrange
        mock_data = [
            ["ID", "Name", "Phone", "Telegram_ID", "Yoga_Experience", 
             "Intensity_Preference", "Time_Preference", "Created_At", "Status"],
            ["client1", "Андрей", "+79991234567", "123456", "Да", 
             "средняя", "утро", "2024-01-01T10:00:00", "active"]
        ]
        
        self.mock_sheets_client.read_range = AsyncMock(return_value=mock_data)
        
        # Act
        result = await self.repository.get_client_by_phone("+79991234567")
        
        # Assert
        assert result is not None
        assert result.name == "Андрей"
        assert result.phone == "+79991234567"
        assert result.yoga_experience is True
    
    @pytest.mark.asyncio
    async def test_get_client_by_phone_not_found(self):
        """Тест поиска клиента по телефону - не найден."""
        # Arrange
        mock_data = [
            ["ID", "Name", "Phone", "Telegram_ID", "Yoga_Experience", 
             "Intensity_Preference", "Time_Preference", "Created_At", "Status"]
        ]
        
        self.mock_sheets_client.read_range = AsyncMock(return_value=mock_data)
        
        # Act
        result = await self.repository.get_client_by_phone("+79999999999")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_client_to_row_conversion(self):
        """Тест преобразования клиента в строку."""
        # Arrange
        from backend.src.models.client import Client
        
        client = Client(
            id="test-id",
            name="Тест",
            phone="+79991234567",
            telegram_id=123456,
            yoga_experience=False,
            intensity_preference="низкая",
            time_preference="вечер",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            status=ClientStatus.ACTIVE
        )
        
        # Act
        row = self.repository._client_to_row(client)
        
        # Assert
        expected_row = [
            "test-id", "Тест", "+79991234567", "123456", "Нет",
            "низкая", "вечер", "2024-01-01T10:00:00", "active",
            "", "", "", ""
        ]
        assert row == expected_row
    
    @pytest.mark.asyncio
    async def test_row_to_client_conversion(self):
        """Тест преобразования строки в клиента."""
        # Arrange
        row = [
            "test-id", "Тест", "+79991234567", "123456", "Да",
            "высокая", "утро", "2024-01-01T10:00:00", "active",
            "25", "Нет травм", "Гибкость", "Интернет"
        ]
        
        # Act
        client = self.repository._row_to_client(row)
        
        # Assert
        assert client is not None
        assert client.id == "test-id"
        assert client.name == "Тест"
        assert client.yoga_experience is True
        assert client.age == 25
        assert client.injuries == "Нет травм"
    
    @pytest.mark.asyncio
    async def test_row_to_client_invalid_data(self):
        """Тест преобразования некорректной строки."""
        # Arrange
        row = ["id", "name"]  # Недостаточно данных
        
        # Act
        client = self.repository._row_to_client(row)
        
        # Assert
        assert client is None
    
    @pytest.mark.asyncio
    async def test_count_clients(self):
        """Тест подсчёта клиентов."""
        # Arrange
        mock_data = [
            ["ID"],
            ["client1"],
            ["client2"],
            [""],  # Пустая строка - не считается
            ["client3"]
        ]
        
        self.mock_sheets_client.read_range = AsyncMock(return_value=mock_data)
        
        # Act
        count = await self.repository.count_clients()
        
        # Assert
        assert count == 3 