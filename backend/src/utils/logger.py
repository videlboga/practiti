"""
📝 Система логирования CyberKitty Practiti

Настройка структурированного логирования с поддержкой различных форматов.
Использует structlog для лучшей структуризации логов.
"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.typing import FilteringBoundLogger

from ..config.settings import settings


def configure_logging() -> None:
    """
    Настройка глобального логирования для приложения.
    
    Использует structlog для структурированных логов.
    """
    # Настройка стандартного logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, settings.log_level.upper()),
        stream=sys.stdout
    )
    
    # Настройка structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Используем JSON в продакшене, читаемый формат в разработке
            structlog.processors.JSONRenderer() if not settings.debug 
            else structlog.dev.ConsoleRenderer(colors=True)
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Получить логгер для модуля.
    
    Args:
        name: Имя модуля (обычно __name__)
        
    Returns:
        Настроенный логгер
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Миксин для добавления логирования в классы.
    
    Автоматически создаёт логгер с именем класса.
    """
    
    @property
    def logger(self) -> FilteringBoundLogger:
        """Получить логгер для этого класса."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_function_call(
    logger: FilteringBoundLogger,
    function_name: str,
    args: Optional[Dict[str, Any]] = None,
    level: str = "info"
) -> None:
    """
    Логирование вызова функции.
    
    Args:
        logger: Логгер для записи
        function_name: Имя функции
        args: Аргументы функции (без чувствительных данных!)
        level: Уровень логирования
    """
    log_method = getattr(logger, level.lower())
    log_method(
        f"Calling {function_name}",
        function=function_name,
        args=args or {}
    )


def log_function_result(
    logger: FilteringBoundLogger,
    function_name: str,
    success: bool,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    level: str = "info"
) -> None:
    """
    Логирование результата функции.
    
    Args:
        logger: Логгер для записи
        function_name: Имя функции
        success: Успешно ли выполнена функция
        result: Результат выполнения (без чувствительных данных!)
        error: Сообщение об ошибке, если есть
        level: Уровень логирования
    """
    log_method = getattr(logger, level.lower())
    
    if success:
        log_method(
            f"Function {function_name} completed successfully",
            function=function_name,
            success=True,
            result=result or {}
        )
    else:
        log_method(
            f"Function {function_name} failed",
            function=function_name,
            success=False,
            error=error
        )


def log_telegram_update(
    logger: FilteringBoundLogger,
    update_type: str,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    message_text: Optional[str] = None
) -> None:
    """
    Логирование Telegram обновлений.
    
    Args:
        logger: Логгер
        update_type: Тип обновления (message, callback_query, и т.д.)
        user_id: ID пользователя
        chat_id: ID чата
        message_text: Текст сообщения (первые 100 символов)
    """
    logger.info(
        f"Telegram update: {update_type}",
        update_type=update_type,
        user_id=user_id,
        chat_id=chat_id,
        message_preview=message_text[:100] if message_text else None
    )


def log_google_sheets_operation(
    logger: FilteringBoundLogger,
    operation: str,
    sheet_name: Optional[str] = None,
    range_name: Optional[str] = None,
    success: bool = True,
    error: Optional[str] = None
) -> None:
    """
    Логирование операций с Google Sheets.
    
    Args:
        logger: Логгер
        operation: Тип операции (read, write, update, и т.д.)
        sheet_name: Имя листа
        range_name: Диапазон ячеек
        success: Успешно ли выполнена операция
        error: Сообщение об ошибке
    """
    level = "info" if success else "error"
    log_method = getattr(logger, level)
    
    log_method(
        f"Google Sheets {operation}",
        operation=operation,
        sheet_name=sheet_name,
        range_name=range_name,
        success=success,
        error=error
    )


def log_client_action(
    logger: FilteringBoundLogger,
    action: str,
    client_id: Optional[str] = None,
    client_phone: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Логирование действий клиентов.
    
    Args:
        logger: Логгер
        action: Действие (registration, subscription_purchase, и т.д.)
        client_id: ID клиента
        client_phone: Телефон клиента (маскированный)
        details: Дополнительные детали
    """
    # Маскируем телефон для логов
    masked_phone = None
    if client_phone:
        masked_phone = client_phone[:3] + "***" + client_phone[-4:]
    
    logger.info(
        f"Client action: {action}",
        action=action,
        client_id=client_id,
        client_phone=masked_phone,
        details=details or {}
    )


def log_subscription_event(
    logger: FilteringBoundLogger,
    event: str,
    subscription_id: str,
    client_id: Optional[str] = None,
    subscription_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Логирование событий абонементов.
    
    Args:
        logger: Логгер
        event: Событие (created, activated, expired, и т.д.)
        subscription_id: ID абонемента
        client_id: ID клиента
        subscription_type: Тип абонемента
        details: Дополнительные детали
    """
    logger.info(
        f"Subscription event: {event}",
        event=event,
        subscription_id=subscription_id,
        client_id=client_id,
        subscription_type=subscription_type,
        details=details or {}
    )


# Инициализация логирования при импорте модуля
configure_logging() 