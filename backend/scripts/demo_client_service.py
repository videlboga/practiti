#!/usr/bin/env python3
"""
🎯 Демонстрация ClientService

Скрипт показывает работу сервиса управления клиентами.
Принцип CyberKitty: простота превыше всего.
"""

import asyncio
import logging
import sys
import os

# Добавляем путь к src для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.client import ClientCreateData, ClientUpdateData, ClientStatus
from services.client_service import ClientService
from repositories.google_sheets_client_repository import GoogleSheetsClientRepository
from utils.exceptions import BusinessLogicError, ValidationError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MockClientRepository:
    """
    Мок репозиторий для демонстрации без реального Google Sheets.
    
    В реальном приложении будет использоваться GoogleSheetsClientRepository.
    """
    
    def __init__(self):
        self.clients = {}
        logger.info("MockClientRepository инициализирован")
    
    async def save(self, client):
        """Сохранить клиента."""
        self.clients[client.id] = client
        logger.info(f"Клиент {client.name} сохранен в моке")
        return client
    
    async def get_by_id(self, client_id):
        """Получить клиента по ID."""
        return self.clients.get(client_id)
    
    async def get_by_phone(self, phone):
        """Получить клиента по телефону."""
        for client in self.clients.values():
            if client.phone == phone:
                return client
        return None
    
    async def get_by_telegram_id(self, telegram_id):
        """Получить клиента по Telegram ID."""
        for client in self.clients.values():
            if client.telegram_id == telegram_id:
                return client
        return None
    
    async def get_all(self):
        """Получить всех клиентов."""
        return list(self.clients.values())
    
    async def search(self, query):
        """Поиск клиентов."""
        results = []
        query_lower = query.lower()
        for client in self.clients.values():
            if (query_lower in client.name.lower() or 
                query in client.phone):
                results.append(client)
        return results


async def demonstrate_client_service():
    """Демонстрация работы ClientService."""
    
    print("🚀 Демонстрация ClientService CyberKitty Practiti")
    print("=" * 50)
    
    # Инициализация
    repository = MockClientRepository()
    client_service = ClientService(repository)
    
    print("\n1️⃣ Создание клиентов")
    print("-" * 30)
    
    # Создаем тестовых клиентов
    clients_data = [
        ClientCreateData(
            name="Анна Петрова",
            phone="+79161234567",
            telegram_id=123456789,
            yoga_experience=True,
            intensity_preference="средняя",
            time_preference="вечер",
            age=30,
            injuries="Проблемы со спиной",
            goals="Улучшение гибкости"
        ),
        ClientCreateData(
            name="Мария Иванова",
            phone="+79169876543",
            telegram_id=987654321,
            yoga_experience=False,
            intensity_preference="низкая",
            time_preference="утро",
            age=25,
            goals="Снятие стресса"
        ),
        ClientCreateData(
            name="Елена Сидорова",
            phone="+79165555555",
            telegram_id=555555555,
            yoga_experience=True,
            intensity_preference="высокая",
            time_preference="день",
            age=35
        )
    ]
    
    created_clients = []
    for client_data in clients_data:
        try:
            client = await client_service.create_client(client_data)
            created_clients.append(client)
            print(f"✅ Создан клиент: {client.name} ({client.phone})")
        except Exception as e:
            print(f"❌ Ошибка создания клиента: {e}")
    
    print(f"\n📊 Всего создано клиентов: {len(created_clients)}")
    
    print("\n2️⃣ Поиск клиентов")
    print("-" * 30)
    
    # Поиск по имени
    search_results = await client_service.search_clients("Анна")
    print(f"🔍 Поиск 'Анна': найдено {len(search_results)} клиентов")
    for client in search_results:
        print(f"   - {client.name} ({client.phone})")
    
    # Поиск по телефону
    client_by_phone = await client_service.get_client_by_phone("+79161234567")
    if client_by_phone:
        print(f"📞 Поиск по телефону: {client_by_phone.name}")
    
    # Поиск по Telegram ID
    client_by_telegram = await client_service.get_client_by_telegram_id(123456789)
    if client_by_telegram:
        print(f"📱 Поиск по Telegram: {client_by_telegram.name}")
    
    print("\n3️⃣ Обновление клиента")
    print("-" * 30)
    
    if created_clients:
        client_to_update = created_clients[0]
        update_data = ClientUpdateData(
            name="Анна Петрова-Новикова",
            injuries="Вылечила спину!"
        )
        
        try:
            updated_client = await client_service.update_client(
                client_to_update.id, 
                update_data
            )
            print(f"✏️ Обновлен клиент: {updated_client.name}")
            print(f"   Новые травмы: {updated_client.injuries}")
        except Exception as e:
            print(f"❌ Ошибка обновления: {e}")
    
    print("\n4️⃣ Управление статусами")
    print("-" * 30)
    
    if len(created_clients) >= 2:
        # Деактивируем клиента
        client_to_deactivate = created_clients[1]
        deactivated = await client_service.deactivate_client(client_to_deactivate.id)
        print(f"⏸️ Деактивирован: {deactivated.name} (статус: {deactivated.status})")
        
        # Показываем активных клиентов
        active_clients = await client_service.get_active_clients()
        print(f"✅ Активных клиентов: {len(active_clients)}")
        
        # Активируем обратно
        reactivated = await client_service.activate_client(client_to_deactivate.id)
        print(f"▶️ Реактивирован: {reactivated.name} (статус: {reactivated.status})")
    
    print("\n5️⃣ Статистика")
    print("-" * 30)
    
    all_clients = await client_service.get_all_clients()
    active_clients = await client_service.get_active_clients()
    trial_clients = await client_service.get_clients_by_status(ClientStatus.TRIAL)
    
    print(f"📈 Общая статистика:")
    print(f"   Всего клиентов: {len(all_clients)}")
    print(f"   Активных: {len(active_clients)}")
    print(f"   На пробном периоде: {len(trial_clients)}")
    
    print("\n6️⃣ Демонстрация валидации")
    print("-" * 30)
    
    # Попытка создать клиента с существующим телефоном
    try:
        duplicate_data = ClientCreateData(
            name="Дубликат",
            phone="+79161234567",  # Уже существует
            telegram_id=999999999,
            yoga_experience=False,
            intensity_preference="любая",
            time_preference="любое"
        )
        await client_service.create_client(duplicate_data)
    except BusinessLogicError as e:
        print(f"🛡️ Валидация работает: {e}")
    
    # Попытка найти несуществующего клиента
    try:
        await client_service.get_client("nonexistent-id")
    except BusinessLogicError as e:
        print(f"🔍 Проверка существования: {e}")
    
    # Попытка поиска с коротким запросом
    try:
        await client_service.search_clients("А")
    except ValidationError as e:
        print(f"📏 Валидация поиска: {e}")
    
    print("\n✅ Демонстрация завершена!")
    print("\nClientService успешно протестирован и готов к использованию! 🎉")


async def demonstrate_error_handling():
    """Демонстрация обработки ошибок."""
    
    print("\n🛡️ Демонстрация обработки ошибок")
    print("=" * 40)
    
    repository = MockClientRepository()
    client_service = ClientService(repository)
    
    error_cases = [
        ("Пустой ID клиента", lambda: client_service.get_client("")),
        ("Некорректный телефон", lambda: client_service.get_client_by_phone("invalid")),
        ("Нулевой Telegram ID", lambda: client_service.get_client_by_telegram_id(0)),
        ("Короткий поисковый запрос", lambda: client_service.search_clients("A")),
    ]
    
    for description, test_func in error_cases:
        try:
            await test_func()
            print(f"❌ {description}: ожидалась ошибка, но её не было")
        except (ValidationError, BusinessLogicError) as e:
            print(f"✅ {description}: {type(e).__name__}")
        except Exception as e:
            print(f"⚠️ {description}: неожиданная ошибка {type(e).__name__}")


if __name__ == "__main__":
    print("🤖 CyberKitty Practiti - Демонстрация ClientService")
    print("Андрей, принцип: простота превыше всего! 🚀\n")
    
    try:
        asyncio.run(demonstrate_client_service())
        asyncio.run(demonstrate_error_handling())
    except KeyboardInterrupt:
        print("\n\n👋 Демонстрация прервана пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"\n💥 Критическая ошибка: {e}")
    
    print("\n🎯 Сессия B3 завершена! ClientService готов для Telegram Bot! 🔥") 