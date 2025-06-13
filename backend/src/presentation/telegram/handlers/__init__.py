"""
📋 Обработчики команд Telegram Bot

Структура handlers согласно архитектуре CyberKitty Practiti.
"""

from .command_handlers import CommandHandlers
from .base_handler import BaseHandler

__all__ = [
    "CommandHandlers",
    "BaseHandler",
] 