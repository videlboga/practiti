"""
🗄️ Временный репозиторий в памяти для тестирования

Используется для отладки бота без подключения к Google Sheets.
"""

from typing import List, Optional, Dict
import uuid
from datetime import datetime

from ..models.client import Client, ClientCreateData, ClientUpdateData, ClientStatus
from ..repositories.protocols.client_repository import ClientRepositoryProtocol
from ..utils.logger import get_logger

logger = get_logger(__name__)


class InMemoryClientRepository(ClientRepositoryProtocol):
    """
    Временный репозиторий клиентов в памяти.
    
    Используется для тестирования без подключения к Google Sheets.
    """
    
    def __init__(self):
        """Инициализация репозитория."""
        self._clients: Dict[str, Client] = {}
        self._phone_index: Dict[str, str] = {}  # phone -> client_id
        self._telegram_index: Dict[int, str] = {}  # telegram_id -> client_id
        
        logger.info("InMemoryClientRepository инициализирован")
    
    async def save_client(self, data: ClientCreateData) -> Client:
        """
        Сохранить нового клиента.
        
        Args:
            data: Данные для создания клиента
            
        Returns:
            Созданный клиент
        """
        client_id = str(uuid.uuid4())
        
        client = Client(
            id=client_id,
            name=data.name,
            phone=data.phone,
            telegram_id=data.telegram_id,
            yoga_experience=data.yoga_experience,
            intensity_preference=data.intensity_preference,
            time_preference=data.time_preference,
            age=data.age,
            injuries=data.injuries,
            goals=data.goals,
            how_found_us=data.how_found_us,
            status=ClientStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Сохраняем клиента
        self._clients[client_id] = client
        self._phone_index[data.phone] = client_id
        self._telegram_index[data.telegram_id] = client_id
        
        logger.info(f"Клиент {client.name} сохранен в памяти с ID: {client_id}")
        return client
    
    async def get_client_by_id(self, client_id: str) -> Optional[Client]:
        """
        Получить клиента по ID.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Клиент или None
        """
        return self._clients.get(client_id)
    
    async def get_client_by_phone(self, phone: str) -> Optional[Client]:
        """
        Получить клиента по телефону.
        
        Args:
            phone: Номер телефона
            
        Returns:
            Клиент или None
        """
        client_id = self._phone_index.get(phone)
        if client_id:
            return self._clients.get(client_id)
        return None
    
    async def get_client_by_telegram_id(self, telegram_id: int) -> Optional[Client]:
        """
        Получить клиента по Telegram ID.
        
        Args:
            telegram_id: Telegram ID
            
        Returns:
            Клиент или None
        """
        client_id = self._telegram_index.get(telegram_id)
        if client_id:
            return self._clients.get(client_id)
        return None
    
    async def update_client(self, client_id: str, data: ClientUpdateData) -> Optional[Client]:
        """
        Обновить клиента.
        
        Args:
            client_id: ID клиента
            data: Данные для обновления
            
        Returns:
            Обновленный клиент или None
        """
        client = self._clients.get(client_id)
        if not client:
            return None
        
        # Обновляем поля
        if data.name is not None:
            client.name = data.name
        if data.phone is not None:
            # Обновляем индекс телефонов
            old_phone = client.phone
            del self._phone_index[old_phone]
            client.phone = data.phone
            self._phone_index[data.phone] = client_id
        if data.status is not None:
            client.status = data.status
        if data.intensity_preference is not None:
            client.intensity_preference = data.intensity_preference
        if data.time_preference is not None:
            client.time_preference = data.time_preference
        if data.age is not None:
            client.age = data.age
        if data.injuries is not None:
            client.injuries = data.injuries
        if data.goals is not None:
            client.goals = data.goals
        
        client.updated_at = datetime.now()
        
        logger.info(f"Клиент {client.name} обновлен в памяти")
        return client
    
    async def search_clients(self, query: str) -> List[Client]:
        """
        Поиск клиентов по имени или телефону.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список найденных клиентов
        """
        query_lower = query.lower()
        results = []
        
        for client in self._clients.values():
            if (query_lower in client.name.lower() or 
                query_lower in client.phone):
                results.append(client)
        
        return results
    
    async def delete_client(self, client_id: str) -> bool:
        """
        Удалить клиента.
        
        Args:
            client_id: ID клиента для удаления
            
        Returns:
            True если клиент удалён, False если не найден
        """
        client = self._clients.get(client_id)
        if not client:
            return False
        
        # Удаляем из всех индексов
        del self._clients[client_id]
        del self._phone_index[client.phone]
        del self._telegram_index[client.telegram_id]
        
        logger.info(f"Клиент {client.name} удален из памяти")
        return True
    
    async def list_clients(
        self, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[Client]:
        """
        Получить список всех клиентов.
        
        Args:
            limit: Максимальное количество клиентов
            offset: Смещение для пагинации
            
        Returns:
            Список клиентов
        """
        clients = list(self._clients.values())
        
        if offset:
            clients = clients[offset:]
        if limit:
            clients = clients[:limit]
            
        return clients
    
    async def count_clients(self) -> int:
        """
        Получить количество клиентов.
        
        Returns:
            Количество клиентов
        """
        return len(self._clients)
    
    def clear_all(self) -> int:
        """
        Очистить все данные (для тестирования).
        
        Returns:
            Количество удаленных записей
        """
        count = len(self._clients)
        self._clients.clear()
        self._phone_index.clear()
        self._telegram_index.clear()
        
        logger.info(f"Очищено {count} клиентов из памяти")
        return count 