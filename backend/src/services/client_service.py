"""
👤 ClientService - бизнес-логика работы с клиентами

Основной сервис для управления клиентами согласно архитектуре CyberKitty Practiti.
Принцип: простота превыше всего.
"""

import logging
from typing import List, Optional

from ..models.client import Client, ClientCreateData, ClientUpdateData, ClientStatus
from ..repositories.protocols import ClientRepositoryProtocol
from ..utils.exceptions import BusinessLogicError, ValidationError
from .protocols.client_service import ClientServiceProtocol

logger = logging.getLogger(__name__)


class ClientService(ClientServiceProtocol):
    """
    Сервис для работы с клиентами.
    
    Реализует всю бизнес-логику управления клиентами:
    - Создание и обновление клиентов
    - Валидация бизнес-правил
    - Поиск и фильтрация
    - Управление статусами
    """
    
    def __init__(self, client_repository: ClientRepositoryProtocol):
        """
        Инициализация сервиса.
        
        Args:
            client_repository: Репозиторий для работы с данными клиентов
        """
        self._repository = client_repository
        logger.info("ClientService инициализирован")
    
    async def create_client(self, data: ClientCreateData) -> Client:
        """
        Создать нового клиента.
        
        Проверяет уникальность телефона и Telegram ID.
        """
        logger.info(f"Создание клиента: {data.name}, {data.phone}")
        
        # Проверяем уникальность телефона
        existing_phone = await self._repository.get_client_by_phone(data.phone)
        if existing_phone:
            logger.warning(f"Клиент с телефоном {data.phone} уже существует")
            raise BusinessLogicError(f"Клиент с телефоном {data.phone} уже зарегистрирован")
        
        # Проверяем уникальность Telegram ID
        existing_telegram = await self._repository.get_client_by_telegram_id(data.telegram_id)
        if existing_telegram:
            logger.warning(f"Клиент с Telegram ID {data.telegram_id} уже существует")
            raise BusinessLogicError(f"Клиент с данным Telegram аккаунтом уже зарегистрирован")
        
        # Сохраняем в репозитории
        saved_client = await self._repository.save_client(data)
        
        logger.info(f"Клиент {saved_client.name} успешно создан с ID: {saved_client.id}")
        return saved_client
    
    async def get_client(self, client_id: str) -> Client:
        """
        Получить клиента по ID.
        """
        logger.debug(f"Получение клиента по ID: {client_id}")
        
        if not client_id:
            raise ValidationError("ID клиента не может быть пустым")
        
        client = await self._repository.get_client_by_id(client_id)
        if not client:
            logger.warning(f"Клиент с ID {client_id} не найден")
            raise BusinessLogicError(f"Клиент с ID {client_id} не найден")
        
        logger.debug(f"Клиент найден: {client.name}")
        return client
    
    async def get_client_by_telegram_id(self, telegram_id: int) -> Optional[Client]:
        """
        Получить клиента по Telegram ID.
        """
        logger.debug(f"Поиск клиента по Telegram ID: {telegram_id}")
        
        if not telegram_id:
            raise ValidationError("Telegram ID не может быть пустым")
        
        client = await self._repository.get_client_by_telegram_id(telegram_id)
        
        if client:
            logger.debug(f"Клиент найден по Telegram ID: {client.name}")
        else:
            logger.debug(f"Клиент с Telegram ID {telegram_id} не найден")
        
        return client
    
    async def get_client_by_phone(self, phone: str) -> Optional[Client]:
        """
        Получить клиента по номеру телефона.
        """
        logger.debug(f"Поиск клиента по телефону: {phone}")
        
        if not phone:
            raise ValidationError("Номер телефона не может быть пустым")
        
        # Нормализуем телефон для поиска
        try:
            # Используем валидатор из модели для нормализации
            normalized_phone = Client.validate_phone(phone)
        except ValueError as e:
            raise ValidationError(f"Некорректный формат телефона: {e}")
        
        client = await self._repository.get_client_by_phone(normalized_phone)
        
        if client:
            logger.debug(f"Клиент найден по телефону: {client.name}")
        else:
            logger.debug(f"Клиент с телефоном {phone} не найден")
        
        return client
    
    async def search_clients(self, query: str) -> List[Client]:
        """
        Поиск клиентов по имени или телефону.
        """
        logger.debug(f"Поиск клиентов по запросу: '{query}'")
        
        if not query or len(query.strip()) < 2:
            raise ValidationError("Поисковый запрос должен содержать минимум 2 символа")
        
        query = query.strip()
        clients = await self._repository.search_clients(query)
        
        logger.info(f"Найдено {len(clients)} клиентов по запросу '{query}'")
        return clients
    
    async def update_client(self, client_id: str, data: ClientUpdateData) -> Client:
        """
        Обновить данные клиента.
        """
        logger.info(f"Обновление клиента ID: {client_id}")
        
        # Получаем существующего клиента
        existing_client = await self.get_client(client_id)
        
        # Проверяем уникальность телефона, если он обновляется
        if data.phone and data.phone != existing_client.phone:
            existing_phone = await self._repository.get_client_by_phone(data.phone)
            if existing_phone:
                logger.warning(f"Телефон {data.phone} уже используется другим клиентом")
                raise BusinessLogicError(f"Телефон {data.phone} уже используется другим клиентом")
        
        # Сохраняем обновления
        saved_client = await self._repository.update_client(client_id, data)
        
        if not saved_client:
            logger.error(f"Не удалось обновить клиента {client_id}")
            raise BusinessLogicError(f"Не удалось обновить клиента {client_id}")
        
        logger.info(f"Клиент {client_id} успешно обновлен")
        return saved_client
    
    async def get_all_clients(self) -> List[Client]:
        """
        Получить всех клиентов.
        """
        logger.debug("Получение всех клиентов")
        
        clients = await self._repository.list_clients()
        
        logger.info(f"Получено {len(clients)} клиентов")
        return clients
    
    async def delete_client(self, client_id: str) -> bool:
        """
        Удалить клиента (мягкое удаление - изменение статуса).
        """
        logger.info(f"Удаление клиента ID: {client_id}")
        
        # Получаем клиента для проверки существования
        client = await self.get_client(client_id)
        
        # Меняем статус на неактивный
        update_data = ClientUpdateData(status=ClientStatus.INACTIVE)
        await self.update_client(client_id, update_data)
        
        logger.info(f"Клиент {client.name} помечен как удаленный")
        return True
    
    async def activate_client(self, client_id: str) -> Client:
        """
        Активировать клиента.
        """
        logger.info(f"Активация клиента ID: {client_id}")
        
        update_data = ClientUpdateData(status=ClientStatus.ACTIVE)
        client = await self.update_client(client_id, update_data)
        
        logger.info(f"Клиент {client.name} активирован")
        return client
    
    async def deactivate_client(self, client_id: str) -> Client:
        """
        Деактивировать клиента.
        """
        logger.info(f"Деактивация клиента ID: {client_id}")
        
        update_data = ClientUpdateData(status=ClientStatus.INACTIVE)
        client = await self.update_client(client_id, update_data)
        
        logger.info(f"Клиент {client.name} деактивирован")
        return client
    
    async def get_active_clients(self) -> List[Client]:
        """
        Получить только активных клиентов.
        
        Дополнительный метод для удобства работы.
        """
        logger.debug("Получение активных клиентов")
        
        all_clients = await self.get_all_clients()
        active_clients = [c for c in all_clients if c.status == ClientStatus.ACTIVE]
        
        logger.info(f"Найдено {len(active_clients)} активных клиентов")
        return active_clients
    
    async def get_clients_by_status(self, status: ClientStatus) -> List[Client]:
        """
        Получить клиентов по статусу.
        
        Args:
            status: Статус клиентов для поиска
            
        Returns:
            Список клиентов с указанным статусом
        """
        logger.debug(f"Поиск клиентов со статусом: {status}")
        
        all_clients = await self.get_all_clients()
        filtered_clients = [c for c in all_clients if c.status == status]
        
        logger.info(f"Найдено {len(filtered_clients)} клиентов со статусом {status}")
        return filtered_clients 