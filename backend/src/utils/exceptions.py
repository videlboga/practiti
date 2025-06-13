"""
🛡️ Базовые исключения для CyberKitty Practiti Backend

Иерархия исключений согласно архитектуре:
- PrakritiException (базовое)
  - ValidationError (ошибки валидации)
  - IntegrationError (ошибки интеграций)
  - BusinessLogicError (ошибки бизнес-логики)
"""

from typing import Optional, Dict, Any


class PrakritiException(Exception):
    """Базовое исключение для всех ошибок CyberKitty Practiti."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(PrakritiException):
    """Ошибки валидации входных данных."""
    
    def __init__(
        self, 
        message: str = "Данные не прошли валидацию",
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
            
        super().__init__(
            message=message,
            details=details,
            error_code=kwargs.get('error_code', 'VALIDATION_ERROR')
        )


class IntegrationError(PrakritiException):
    """Ошибки интеграции с внешними системами."""
    
    def __init__(
        self, 
        message: str = "Ошибка интеграции с внешней системой",
        service: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if service:
            details['service'] = service
            
        super().__init__(
            message=message,
            details=details,
            error_code=kwargs.get('error_code', 'INTEGRATION_ERROR')
        )


class BusinessLogicError(PrakritiException):
    """Ошибки бизнес-логики."""
    
    def __init__(
        self, 
        message: str = "Нарушение бизнес-правил",
        rule: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if rule:
            details['rule'] = rule
            
        super().__init__(
            message=message,
            details=details,
            error_code=kwargs.get('error_code', 'BUSINESS_LOGIC_ERROR')
        )


# Специфичные исключения

class ClientNotFoundError(BusinessLogicError):
    """Клиент не найден."""
    
    def __init__(self, client_id: str):
        super().__init__(
            message=f"Клиент с ID {client_id} не найден",
            error_code="CLIENT_NOT_FOUND",
            details={'client_id': client_id}
        )


class SubscriptionNotFoundError(BusinessLogicError):
    """Абонемент не найден."""
    
    def __init__(self, subscription_id: str):
        super().__init__(
            message=f"Абонемент с ID {subscription_id} не найден",
            error_code="SUBSCRIPTION_NOT_FOUND",
            details={'subscription_id': subscription_id}
        )


class InsufficientClassesError(BusinessLogicError):
    """Недостаточно занятий в абонементе."""
    
    def __init__(self, remaining_classes: int):
        super().__init__(
            message=f"Недостаточно занятий. Осталось: {remaining_classes}",
            error_code="INSUFFICIENT_CLASSES",
            details={'remaining_classes': remaining_classes}
        )


class ExpiredSubscriptionError(BusinessLogicError):
    """Абонемент истёк."""
    
    def __init__(self, subscription_id: str, end_date: str):
        super().__init__(
            message=f"Абонемент {subscription_id} истёк {end_date}",
            error_code="EXPIRED_SUBSCRIPTION",
            details={'subscription_id': subscription_id, 'end_date': end_date}
        )


class GoogleSheetsError(IntegrationError):
    """Ошибки работы с Google Sheets."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            service="google_sheets",
            error_code="GOOGLE_SHEETS_ERROR",
            details={'operation': operation} if operation else {}
        )


class TelegramBotError(IntegrationError):
    """Ошибки работы с Telegram Bot API."""
    
    def __init__(self, message: str, chat_id: Optional[int] = None):
        super().__init__(
            message=message,
            service="telegram_bot",
            error_code="TELEGRAM_BOT_ERROR",
            details={'chat_id': chat_id} if chat_id else {}
        ) 