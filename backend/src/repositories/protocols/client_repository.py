"""
👤 Протокол репозитория клиентов CyberKitty Practiti

Интерфейс для работы с данными клиентов в любом хранилище.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ...models.client import Client, ClientCreateData, ClientUpdateData


class ClientRepositoryProtocol(ABC):
    """
    Протокол репозитория для работы с клиентами.
    
    Определяет интерфейс для всех операций с данными клиентов.
    """
    
    @abstractmethod
    async def save_client(self, data: ClientCreateData) -> Client:
        """
        Сохранить нового клиента.
        
        Args:
            data: Данные для создания клиента
            
        Returns:
            Созданный клиент с присвоенным ID
        """
        pass
    
    @abstractmethod
    async def get_client_by_id(self, client_id: str) -> Optional[Client]:
        """
        Получить клиента по ID.
        
        Args:
            client_id: Уникальный ID клиента
            
        Returns:
            Клиент или None если не найден
        """
        pass
    
    @abstractmethod
    async def get_client_by_phone(self, phone: str) -> Optional[Client]:
        """
        Получить клиента по номеру телефона.
        
        Args:
            phone: Номер телефона клиента
            
        Returns:
            Клиент или None если не найден
        """
        pass
    
    @abstractmethod
    async def get_client_by_telegram_id(self, telegram_id: int) -> Optional[Client]:
        """
        Получить клиента по Telegram ID.
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            Клиент или None если не найден
        """
        pass
    
    @abstractmethod
    async def update_client(self, client_id: str, data: ClientUpdateData) -> Optional[Client]:
        """
        Обновить данные клиента.
        
        Args:
            client_id: ID клиента для обновления
            data: Новые данные клиента
            
        Returns:
            Обновлённый клиент или None если не найден
        """
        pass
    
    @abstractmethod
    async def delete_client(self, client_id: str) -> bool:
        """
        Удалить клиента.
        
        Args:
            client_id: ID клиента для удаления
            
        Returns:
            True если клиент удалён, False если не найден
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def search_clients(self, query: str) -> List[Client]:
        """
        Поиск клиентов по имени или телефону.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список найденных клиентов
        """
        pass
    
    @abstractmethod
    async def count_clients(self) -> int:
        """
        Получить общее количество клиентов.
        
        Returns:
            Количество клиентов
        """
        pass 