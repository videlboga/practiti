"""
🛠️ Скрипт для настройки Google-таблицы CyberKitty Practiti

Этот скрипт выполняет следующие действия:
1. Подключается к Google-таблице, указанной в настройках.
2. Проверяет наличие листов: "Clients", "Subscriptions", "Notifications".
3. Если листы отсутствуют, создает их.
4. Записывает правильные заголовки в первую строку каждого листа.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path для корректного импорта
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Теперь можно импортировать модули проекта
from backend.src.integrations.google_sheets import GoogleSheetsClient
from backend.src.repositories.google_sheets_client_repository import GoogleSheetsClientRepository
from backend.src.repositories.google_sheets_subscription_repository import GoogleSheetsSubscriptionRepository
from backend.src.repositories.google_sheets_notification_repository import GoogleSheetsNotificationRepository

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def setup_google_sheets():
    """
    Основная функция для создания и настройки листов в Google-таблице.
    """
    logger.info("🚀 Запуск скрипта настройки Google-таблицы...")
    
    try:
        client = GoogleSheetsClient()
        service = client.service  # Аутентификация и получение сервиса
        spreadsheet_id = client.spreadsheet_id
        
        logger.info(f"✅ Успешно подключились к таблице ID: {spreadsheet_id}")
        
        # 1. Получаем информацию о существующих листах
        spreadsheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet_metadata.get('sheets', [])
        existing_sheet_titles = {s.get('properties', {}).get('title') for s in sheets}
        logger.info(f"Найденные листы: {list(existing_sheet_titles)}")

        # 2. Определяем, какие листы и заголовки нам нужны
        required_sheets = {
            "Clients": GoogleSheetsClientRepository.HEADER_ROW,
            "Subscriptions": GoogleSheetsSubscriptionRepository.HEADER_ROW,
            "Notifications": GoogleSheetsNotificationRepository.HEADER_ROW,
        }
        
        # 3. Формируем запросы на создание недостающих листов
        batch_update_requests = []
        for title in required_sheets:
            if title not in existing_sheet_titles:
                logger.warning(f"Лист '{title}' не найден. Будет создан.")
                batch_update_requests.append({'addSheet': {'properties': {'title': title}}})
        
        # 4. Создаем недостающие листы одним запросом
        if batch_update_requests:
            logger.info("Выполняется пакетное создание листов...")
            body = {'requests': batch_update_requests}
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
            logger.info("✅ Недостающие листы успешно созданы.")
        else:
            logger.info("Все необходимые листы уже существуют.")

        # 5. Записываем заголовки в каждый лист
        logger.info("Проверка и запись заголовков...")
        for title, headers in required_sheets.items():
            range_name = f"{title}!A1"
            try:
                await client.write_range(range_name="A1", values=[headers], sheet_name=title)
                logger.info(f" -> Заголовки для листа '{title}' успешно записаны.")
            except Exception as e:
                logger.error(f"Не удалось записать заголовки для '{title}': {e}")
        
        logger.info("✅🏁 Настройка Google-таблицы успешно завершена!")

    except Exception as e:
        logger.critical(f"❌ КРИТИЧЕСКАЯ ОШИБКА во время настройки: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Запускаем асинхронную функцию
    asyncio.run(setup_google_sheets()) 