"""
🔌 Протокол ClientService

Интерфейс для работы с клиентами согласно архитектуре CyberKitty Practiti.
"""

from typing import List, Optional, Protocol

from ...models.client import Client, ClientCreateData, ClientUpdateData


class ClientServiceProtocol(Protocol):
    """
    Протокол сервиса для работы с клиентами.
    
    Определяет все методы бизнес-логики для управления клиентами.
    Следует принципам CyberKitty: простота превыше всего.
    """
    
    async def create_client(self, data: ClientCreateData) -> Client:
        """
        Создать нового клиента.
        
        Args:
            data: Данные для создания клиента
            
        Returns:
            Созданный клиент
            
        Raises:
            ValidationError: Некорректные данные
            BusinessLogicError: Клиент уже существует
            IntegrationError: Ошибка сохранения
        """
        ...
    
    async def get_client(self, client_id: str) -> Client:
        """
        Получить клиента по ID.
        
        Args:
            client_id: Уникальный ID клиента
            
        Returns:
            Найденный клиент
            
        Raises:
            BusinessLogicError: Клиент не найден
            IntegrationError: Ошибка доступа к данным
        """
        ...
    
    async def get_client_by_telegram_id(self, telegram_id: int) -> Optional[Client]:
        """
        Получить клиента по Telegram ID.
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            Найденный клиент или None
            
        Raises:
            IntegrationError: Ошибка доступа к данным
        """
        ...
    
    async def get_client_by_phone(self, phone: str) -> Optional[Client]:
        """
        Получить клиента по номеру телефона.
        
        Args:
            phone: Номер телефона клиента
            
        Returns:
            Найденный клиент или None
            
        Raises:
            IntegrationError: Ошибка доступа к данным
        """
        ...
    
    async def search_clients(self, query: str) -> List[Client]:
        """
        Поиск клиентов по имени или телефону.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список найденных клиентов
            
        Raises:
            IntegrationError: Ошибка доступа к данным
        """
        ...
    
    async def update_client(self, client_id: str, data: ClientUpdateData) -> Client:
        """
        Обновить данные клиента.
        
        Args:
            client_id: ID клиента для обновления
            data: Новые данные клиента
            
        Returns:
            Обновленный клиент
            
        Raises:
            ValidationError: Некорректные данные
            BusinessLogicError: Клиент не найден
            IntegrationError: Ошибка сохранения
        """
        ...
    
    async def get_all_clients(self) -> List[Client]:
        """
        Получить всех клиентов.
        
        Returns:
            Список всех клиентов
            
        Raises:
            IntegrationError: Ошибка доступа к данным
        """
        ...
    
    async def delete_client(self, client_id: str) -> bool:
        """
        Удалить клиента (мягкое удаление - изменение статуса).
        
        Args:
            client_id: ID клиента для удаления
            
        Returns:
            True если успешно удален
            
        Raises:
            BusinessLogicError: Клиент не найден
            IntegrationError: Ошибка сохранения
        """
        ...
    
    async def activate_client(self, client_id: str) -> Client:
        """
        Активировать клиента.
        
        Args:
            client_id: ID клиента для активации
            
        Returns:
            Активированный клиент
            
        Raises:
            BusinessLogicError: Клиент не найден
            IntegrationError: Ошибка сохранения
        """
        ...
    
    async def deactivate_client(self, client_id: str) -> Client:
        """
        Деактивировать клиента.
        
        Args:
            client_id: ID клиента для деактивации
            
        Returns:
            Деактивированный клиент
            
        Raises:
            BusinessLogicError: Клиент не найден
            IntegrationError: Ошибка сохранения
        """
        ... 