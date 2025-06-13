"""
📊 Google Sheets API клиент для CyberKitty Practiti

Интеграция с Google Sheets API для хранения данных о клиентах,
абонементах и записях на занятия.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config.settings import settings
from ..utils.logger import get_logger, log_google_sheets_operation
from ..utils.exceptions import GoogleSheetsError

logger = get_logger(__name__)


class GoogleSheetsClient:
    """
    Клиент для работы с Google Sheets API.
    
    Обеспечивает базовые операции чтения и записи данных.
    """
    
    def __init__(self, credentials_file: Optional[str] = None, spreadsheet_id: Optional[str] = None):
        """
        Инициализация клиента Google Sheets.
        
        Args:
            credentials_file: Путь к файлу с credentials
            spreadsheet_id: ID таблицы Google Sheets
        """
        self.credentials_file = credentials_file or settings.google_credentials_path
        self.spreadsheet_id = spreadsheet_id or settings.google_sheets_id
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.readonly']
        
        self._service = None
        self._credentials = None
        
        logger.info(
            "Initializing Google Sheets client",
            spreadsheet_id=self.spreadsheet_id,
            credentials_file=self.credentials_file
        )
    
    @property
    def service(self):
        """Получить сервис Google Sheets API с ленивой инициализацией."""
        if self._service is None:
            self._authenticate()
        return self._service
    
    def _authenticate(self) -> None:
        """Аутентификация в Google Sheets API."""
        try:
            logger.info("Authenticating with Google Sheets API")
            
            # Проверяем существование файла credentials
            credentials_path = Path(self.credentials_file)
            if not credentials_path.exists():
                raise GoogleSheetsError(
                    f"Credentials file not found: {self.credentials_file}",
                    operation="authentication"
                )
            
            # Загружаем credentials
            self._credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.scopes
            )
            
            # Создаём сервис
            self._service = build('sheets', 'v4', credentials=self._credentials)
            
            log_google_sheets_operation(
                logger,
                operation="authentication",
                success=True
            )
            
        except FileNotFoundError as e:
            error_msg = f"Credentials file not found: {e}"
            log_google_sheets_operation(
                logger,
                operation="authentication",
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="authentication")
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid credentials file format: {e}"
            log_google_sheets_operation(
                logger,
                operation="authentication",
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="authentication")
            
        except Exception as e:
            error_msg = f"Authentication failed: {e}"
            log_google_sheets_operation(
                logger,
                operation="authentication",
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="authentication")
    
    async def read_range(self, range_name: str, sheet_name: str = "Sheet1") -> List[List[str]]:
        """
        Чтение данных из указанного диапазона.
        
        Args:
            range_name: Диапазон ячеек (например, "A1:E10")
            sheet_name: Имя листа
            
        Returns:
            Список строк с данными
        """
        full_range = f"{sheet_name}!{range_name}"
        
        try:
            logger.info(f"Reading range: {full_range}")
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=full_range
            ).execute()
            
            values = result.get('values', [])
            
            log_google_sheets_operation(
                logger,
                operation="read",
                sheet_name=sheet_name,
                range_name=range_name,
                success=True
            )
            
            return values
            
        except HttpError as e:
            error_msg = f"HTTP error reading range {full_range}: {e}"
            log_google_sheets_operation(
                logger,
                operation="read",
                sheet_name=sheet_name,
                range_name=range_name,
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="read")
            
        except Exception as e:
            error_msg = f"Unexpected error reading range {full_range}: {e}"
            log_google_sheets_operation(
                logger,
                operation="read",
                sheet_name=sheet_name,
                range_name=range_name,
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="read")
    
    async def write_range(
        self, 
        range_name: str, 
        values: List[List[Any]], 
        sheet_name: str = "Sheet1"
    ) -> bool:
        """
        Запись данных в указанный диапазон.
        
        Args:
            range_name: Диапазон ячеек
            values: Данные для записи
            sheet_name: Имя листа
            
        Returns:
            True если запись успешна
        """
        full_range = f"{sheet_name}!{range_name}"
        
        try:
            logger.info(f"Writing to range: {full_range}")
            
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=full_range,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            
            log_google_sheets_operation(
                logger,
                operation="write",
                sheet_name=sheet_name,
                range_name=range_name,
                success=True
            )
            
            logger.info(f"Updated {updated_cells} cells in {full_range}")
            return True
            
        except HttpError as e:
            error_msg = f"HTTP error writing to range {full_range}: {e}"
            log_google_sheets_operation(
                logger,
                operation="write",
                sheet_name=sheet_name,
                range_name=range_name,
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="write")
            
        except Exception as e:
            error_msg = f"Unexpected error writing to range {full_range}: {e}"
            log_google_sheets_operation(
                logger,
                operation="write",
                sheet_name=sheet_name,
                range_name=range_name,
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="write")
    
    async def append_rows(
        self, 
        values: List[List[Any]], 
        sheet_name: str = "Sheet1"
    ) -> bool:
        """
        Добавление строк в конец таблицы.
        
        Args:
            values: Данные для добавления
            sheet_name: Имя листа
            
        Returns:
            True если добавление успешно
        """
        try:
            logger.info(f"Appending {len(values)} rows to {sheet_name}")
            
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:A",
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            updated_cells = result.get('updates', {}).get('updatedCells', 0)
            
            log_google_sheets_operation(
                logger,
                operation="append",
                sheet_name=sheet_name,
                success=True
            )
            
            logger.info(f"Appended {updated_cells} cells to {sheet_name}")
            return True
            
        except HttpError as e:
            error_msg = f"HTTP error appending to {sheet_name}: {e}"
            log_google_sheets_operation(
                logger,
                operation="append",
                sheet_name=sheet_name,
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="append")
            
        except Exception as e:
            error_msg = f"Unexpected error appending to {sheet_name}: {e}"
            log_google_sheets_operation(
                logger,
                operation="append",
                sheet_name=sheet_name,
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="append")
    
    async def clear_range(self, range_name: str, sheet_name: str = "Sheet1") -> bool:
        """
        Очистка указанного диапазона.
        
        Args:
            range_name: Диапазон для очистки
            sheet_name: Имя листа
            
        Returns:
            True если очистка успешна
        """
        full_range = f"{sheet_name}!{range_name}"
        
        try:
            logger.info(f"Clearing range: {full_range}")
            
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=full_range
            ).execute()
            
            log_google_sheets_operation(
                logger,
                operation="clear",
                sheet_name=sheet_name,
                range_name=range_name,
                success=True
            )
            
            return True
            
        except HttpError as e:
            error_msg = f"HTTP error clearing range {full_range}: {e}"
            log_google_sheets_operation(
                logger,
                operation="clear",
                sheet_name=sheet_name,
                range_name=range_name,
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="clear")
            
        except Exception as e:
            error_msg = f"Unexpected error clearing range {full_range}: {e}"
            log_google_sheets_operation(
                logger,
                operation="clear",
                sheet_name=sheet_name,
                range_name=range_name,
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="clear")
    
    async def get_sheet_info(self) -> Dict[str, Any]:
        """
        Получение информации о таблице.
        
        Returns:
            Информация о таблице и листах
        """
        try:
            logger.info("Getting spreadsheet info")
            
            result = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            log_google_sheets_operation(
                logger,
                operation="get_info",
                success=True
            )
            
            return result
            
        except HttpError as e:
            error_msg = f"HTTP error getting spreadsheet info: {e}"
            log_google_sheets_operation(
                logger,
                operation="get_info",
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="get_info")
            
        except Exception as e:
            error_msg = f"Unexpected error getting spreadsheet info: {e}"
            log_google_sheets_operation(
                logger,
                operation="get_info",
                success=False,
                error=error_msg
            )
            raise GoogleSheetsError(error_msg, operation="get_info") 