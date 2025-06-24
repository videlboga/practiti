"""
📅 Booking Handlers for Telegram Bot – Practiti

Позволяет клиентам записываться на занятия командой /book.
Простая реализация: бот запрашивает дату, время и тип занятия одной строкой,
после чего создаёт запись через BookingService и сообщает результат.

Формат ввода: YYYY-MM-DD HH:MM <тип>
Пример: 2025-07-01 19:00 хатха

TODO: расширить на выбор из расписания, inline-кнопки и подтверждение.
"""

from __future__ import annotations

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, filters, MessageHandler, CommandHandler

from .base_handler import BaseHandler
from ....services.protocols.booking_service import BookingServiceProtocol
from ....services.protocols.client_service import ClientServiceProtocol
from ....models.booking import BookingCreateData
from ....utils.exceptions import BusinessLogicError

logger = logging.getLogger(__name__)

# Состояния ConversationHandler
BOOKING_INPUT = 1


class BookingHandlers(BaseHandler):
    """Обработчики команды /book и связанных шагов."""

    def __init__(self, booking_service: BookingServiceProtocol, client_service: ClientServiceProtocol):
        super().__init__(client_service)
        self.booking_service = booking_service
        logger.info("BookingHandlers инициализирован")

    # ---------------------------------------------------------------------
    #   /book – начальная точка
    # ---------------------------------------------------------------------

    async def book_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:  # type: ignore[override]
        """Старт обработки /book.

        1. Проверяем, зарегистрирован ли пользователь.
        2. Просим ввести дату, время и тип занятия одной строкой.
        """
        await self.log_command(update, "book")

        try:
            user_id, username, first_name = await self.get_user_info(update)
            client = await self.client_service.get_client_by_telegram_id(user_id)

            if not client:
                msg = (
                    "📝 Сначала пройдите регистрацию в студии.\n"
                    "Используйте /register, это займёт пару минут."
                )
                if update.effective_chat:
                    await update.effective_chat.send_message(msg)
                return ConversationHandler.END

            prompt = (
                "📅 Введите *дату*, *время* и *тип* занятия через пробел.\n\n"
                "Формат: `YYYY-MM-DD HH:MM тип`\n"
                "Пример: `2025-07-01 19:00 хатха`"
            )
            if update.effective_chat:
                await update.effective_chat.send_message(prompt, parse_mode="Markdown")
            return BOOKING_INPUT
        except Exception as e:
            await self.handle_error(update, context, e)
            return ConversationHandler.END

    # ------------------------------------------------------------------
    #   Обработка ввода пользователя
    # ------------------------------------------------------------------

    async def process_booking_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:  # type: ignore[override]
        if not update.message or not update.message.text:
            return BOOKING_INPUT

        text = update.message.text.strip()
        parts = text.split()
        if len(parts) < 3:
            await update.effective_chat.send_message(
                "❌ Неверный формат. Попробуйте ещё раз или /cancel." )
            return BOOKING_INPUT

        date_part, time_part, *class_type_parts = parts
        class_type = " ".join(class_type_parts)

        try:
            class_dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
        except ValueError:
            await update.effective_chat.send_message(
                "❌ Не удалось разобрать дату/время. Используйте формат YYYY-MM-DD HH:MM.")
            return BOOKING_INPUT

        # Проверяем клиента
        user_id = update.effective_user.id  # type: ignore[assignment]
        client = await self.client_service.get_client_by_telegram_id(user_id)
        if not client:
            await update.effective_chat.send_message("❌ Клиент не найден. Пройдите регистрацию /register.")
            return ConversationHandler.END

        # Формируем данные записи
        create_data = BookingCreateData(
            client_id=client.id,
            class_date=class_dt,
            class_type=class_type,
        )

        try:
            booking = await self.booking_service.create_booking(create_data)
            await update.effective_chat.send_message(
                f"✅ Запись создана! До встречи {class_dt.strftime('%d.%m %H:%M')} ✨")
            logger.info("Создана запись %s через Telegram для клиента %s", booking.id, client.id)
        except (ValueError, BusinessLogicError) as be:
            await update.effective_chat.send_message(f"🚫 Не удалось создать запись: {be}")
        except Exception as e:
            logger.exception("Ошибка создания бронирования: %s", e)
            await update.effective_chat.send_message("🚫 Произошла ошибка. Попробуйте позже.")

        return ConversationHandler.END

    # ------------------------------------------------------------------
    #   Отмена диалога
    # ------------------------------------------------------------------

    async def cancel_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:  # type: ignore[override]
        if update.effective_chat:
            await update.effective_chat.send_message("❌ Запись отменена.")
        return ConversationHandler.END

    # ------------------------------------------------------------------
    #   Реализация абстрактного метода BaseHandler
    # ------------------------------------------------------------------

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # type: ignore[override]
        """По умолчанию перенаправляем на book_command.

        Этот метод необходим лишь для соответствия абстрактному контракту
        BaseHandler, так как BookingHandlers работает через ConversationHandler
        с отдельными методами. Если класс используется напрямую (напр. в тестах),
        достаточно вызвать стартовую логику /book.
        """
        await self.book_command(update, context) 