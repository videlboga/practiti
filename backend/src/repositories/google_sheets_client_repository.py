"""
👤 Google Sheets репозиторий клиентов CyberKitty Practiti

Реализация ClientRepositoryProtocol для хранения данных в Google Sheets.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from ..integrations.google_sheets import GoogleSheetsClient
from ..models.client import Client, ClientCreateData, ClientUpdateData, ClientStatus
from ..utils.logger import get_logger, log_client_action
from ..utils.exceptions import GoogleSheetsError, ClientNotFoundError
from .protocols.client_repository import ClientRepositoryProtocol

logger = get_logger(__name__)


class GoogleSheetsClientRepository(ClientRepositoryProtocol):
    """
    Репозиторий клиентов для Google Sheets.
    
    Структура листа "Clients":
    A: ID | B: Name | C: Phone | D: Telegram_ID | E: Yoga_Experience | 
    F: Intensity_Preference | G: Time_Preference | H: Created_At | I: Status |
    J: Age | K: Injuries | L: Goals | M: How_Found_Us
    """
    
    SHEET_NAME = "Clients"
    HEADER_ROW = [
        "ID", "Name", "Phone", "Telegram_ID", "Yoga_Experience",
        "Intensity_Preference", "Time_Preference", "Created_At", "Status",
        "Age", "Injuries", "Goals", "How_Found_Us"
    ]
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        """
        Инициализация репозитория.
        
        Args:
            sheets_client: Клиент для работы с Google Sheets
        """
        self.sheets_client = sheets_client
        logger.info("Initialized Google Sheets Client Repository")
    
    async def _ensure_headers(self) -> None:
        """Убедиться, что заголовки таблицы установлены."""
        # Убеждаемся, что лист существует
        await self.sheets_client.ensure_sheet_exists(self.SHEET_NAME)

        try:
            # Читаем первую строку
            first_row = await self.sheets_client.read_range("A1:M1", self.SHEET_NAME)
            
            # Если заголовков нет или они неправильные, устанавливаем их
            if not first_row or first_row[0] != self.HEADER_ROW:
                await self.sheets_client.write_range(
                    "A1:M1", 
                    [self.HEADER_ROW], 
                    self.SHEET_NAME
                )
                logger.info("Headers set for Clients sheet")
                
        except GoogleSheetsError:
            # Если лист не существует или другая ошибка – пытаемся записать заголовки
            await self.sheets_client.write_range("A1:M1", [self.HEADER_ROW], self.SHEET_NAME)
            logger.info("Created Clients sheet with headers")
    
    def _client_to_row(self, client: Client) -> List[str]:
        """
        Преобразовать модель клиента в строку для Google Sheets.
        
        Args:
            client: Модель клиента
            
        Returns:
            Список значений для строки таблицы
        """
        return [
            client.id,
            client.name,
            client.phone,
            str(client.telegram_id) if client.telegram_id is not None else "",
            "Да" if client.yoga_experience else "Нет",
            client.intensity_preference,
            client.time_preference,
            client.created_at.isoformat(),
            client.status.value,
            str(client.age) if client.age else "",
            client.injuries or "",
            client.goals or "",
            client.how_found_us or ""
        ]
    
    def _row_to_client(self, row: List[str]) -> Optional[Client]:
        """
        Преобразовать строку из Google Sheets в модель клиента.
        
        Args:
            row: Строка данных из таблицы
            
        Returns:
            Модель клиента или None если данные некорректны
        """
        try:
            if len(row) < 9:  # Минимум обязательных полей
                return None
            
            return Client(
                id=row[0],
                name=row[1],
                phone=row[2],
                telegram_id=int(row[3]) if row[3] else None,
                yoga_experience=row[4].lower() in ["да", "yes", "true", "1"],
                intensity_preference=row[5],
                time_preference=row[6],
                created_at=datetime.fromisoformat(row[7]),
                status=ClientStatus(row[8]) if row[8] else ClientStatus.ACTIVE,
                age=int(row[9]) if len(row) > 9 and row[9] else None,
                injuries=row[10] if len(row) > 10 and row[10] else None,
                goals=row[11] if len(row) > 11 and row[11] else None,
                how_found_us=row[12] if len(row) > 12 and row[12] else None
            )
            
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing client row: {e}", row=row)
            return None
    
    async def _find_client_row(self, client_id: str) -> Optional[int]:
        """
        Найти номер строки клиента по ID.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Номер строки (начиная с 1) или None если не найден
        """
        try:
            # Читаем все ID клиентов (колонка A)
            ids_data = await self.sheets_client.read_range("A:A", self.SHEET_NAME)
            
            for row_num, row in enumerate(ids_data, 1):
                if row and row[0] == client_id:
                    return row_num
            
            return None
            
        except GoogleSheetsError:
            return None
    
    async def save_client(self, data: ClientCreateData) -> Client:
        """Сохранить нового клиента."""
        await self._ensure_headers()
        
        # Создаём модель клиента
        client = Client(**data.model_dump())
        
        try:
            # Добавляем строку в конец таблицы
            row_data = self._client_to_row(client)
            await self.sheets_client.append_rows([row_data], self.SHEET_NAME)
            
            log_client_action(
                logger,
                action="created",
                client_id=client.id,
                client_phone=client.phone
            )
            
            return client
            
        except GoogleSheetsError as e:
            logger.error(f"Failed to save client: {e}")
            raise
    
    async def get_client_by_id(self, client_id: str) -> Optional[Client]:
        """Получить клиента по ID."""
        try:
            row_num = await self._find_client_row(client_id)
            if not row_num:
                return None
            
            # Читаем данные клиента
            client_data = await self.sheets_client.read_range(
                f"A{row_num}:M{row_num}", 
                self.SHEET_NAME
            )
            
            if not client_data or not client_data[0]:
                return None
            
            return self._row_to_client(client_data[0])
            
        except GoogleSheetsError as e:
            logger.error(f"Failed to get client by ID {client_id}: {e}")
            return None
    
    async def get_client_by_phone(self, phone: str) -> Optional[Client]:
        """Получить клиента по номеру телефона."""
        try:
            # Читаем все данные клиентов
            all_data = await self.sheets_client.read_range("A:M", self.SHEET_NAME)
            
            # Пропускаем заголовок
            for row in all_data[1:]:
                if len(row) >= 3 and row[2] == phone:
                    return self._row_to_client(row)
            
            return None
            
        except GoogleSheetsError as e:
            logger.error(f"Failed to get client by phone {phone}: {e}")
            return None
    
    async def get_client_by_telegram_id(self, telegram_id: int) -> Optional[Client]:
        """Получить клиента по Telegram ID."""
        if telegram_id is None:
            return None
        try:
            # Читаем все данные клиентов
            all_data = await self.sheets_client.read_range("A:M", self.SHEET_NAME)
            
            # Пропускаем заголовок
            for row in all_data[1:]:
                if len(row) >= 4 and row[3] == str(telegram_id):
                    return self._row_to_client(row)
            
            return None
            
        except GoogleSheetsError as e:
            logger.error(f"Failed to get client by telegram_id {telegram_id}: {e}")
            return None
    
    async def update_client(self, client_id: str, data: ClientUpdateData) -> Optional[Client]:
        """Обновить данные клиента."""
        try:
            # Находим клиента
            existing_client = await self.get_client_by_id(client_id)
            if not existing_client:
                return None
            
            # Обновляем данные
            update_dict = data.model_dump(exclude_unset=True)
            updated_client = existing_client.model_copy(update=update_dict)
            
            # Находим строку для обновления
            row_num = await self._find_client_row(client_id)
            if not row_num:
                return None
            
            # Записываем обновлённые данные
            row_data = self._client_to_row(updated_client)
            await self.sheets_client.write_range(
                f"A{row_num}:M{row_num}",
                [row_data],
                self.SHEET_NAME
            )
            
            log_client_action(
                logger,
                action="updated",
                client_id=client_id,
                details=update_dict
            )
            
            return updated_client
            
        except GoogleSheetsError as e:
            logger.error(f"Failed to update client {client_id}: {e}")
            return None
    
    async def delete_client(self, client_id: str) -> bool:
        """Удалить клиента."""
        try:
            row_num = await self._find_client_row(client_id)
            if not row_num:
                return False
            
            # Очищаем строку (Google Sheets API не поддерживает удаление строк напрямую)
            await self.sheets_client.clear_range(
                f"A{row_num}:M{row_num}",
                self.SHEET_NAME
            )
            
            log_client_action(
                logger,
                action="deleted",
                client_id=client_id
            )
            
            return True
            
        except GoogleSheetsError as e:
            logger.error(f"Failed to delete client {client_id}: {e}")
            return False
    
    async def list_clients(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[Client]:
        """Получить список всех клиентов."""
        try:
            # Читаем все данные клиентов
            all_data = await self.sheets_client.read_range("A:M", self.SHEET_NAME)
            
            clients = []
            # Пропускаем заголовок
            for row in all_data[1:]:
                if row and row[0]:  # Проверяем, что строка не пустая
                    client = self._row_to_client(row)
                    if client:
                        clients.append(client)
            
            # Применяем offset и limit
            if offset:
                clients = clients[offset:]
            if limit:
                clients = clients[:limit]
            
            return clients
            
        except GoogleSheetsError as e:
            logger.error(f"Failed to list clients: {e}")
            return []
    
    async def search_clients(self, query: str) -> List[Client]:
        """Поиск клиентов по имени или телефону."""
        try:
            all_clients = await self.list_clients()
            query_lower = query.lower()
            
            matching_clients = []
            for client in all_clients:
                if (query_lower in client.name.lower() or 
                    query in client.phone):
                    matching_clients.append(client)
            
            return matching_clients
            
        except Exception as e:
            logger.error(f"Failed to search clients: {e}")
            return []
    
    async def count_clients(self) -> int:
        """Получить общее количество клиентов."""
        try:
            # Читаем колонку ID
            ids_data = await self.sheets_client.read_range("A:A", self.SHEET_NAME)
            
            # Считаем непустые строки (исключая заголовок)
            count = 0
            for row in ids_data[1:]:
                if row and row[0]:
                    count += 1
            
            return count
            
        except GoogleSheetsError as e:
            logger.error(f"Failed to count clients: {e}")
            return 0 