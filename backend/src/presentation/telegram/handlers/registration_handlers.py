"""
📝 Обработчики регистрации CyberKitty Practiti

Handlers для пошагового анкетирования новых пользователей.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from .base_handler import BaseHandler
from ....models.registration import RegistrationState, REGISTRATION_STEPS
from ....services.registration_service import RegistrationService
from ....utils.logger import get_logger
from ....utils.exceptions import ValidationError, BusinessLogicError
from .. import templates as tpl

logger = get_logger(__name__)

# Состояния для ConversationHandler регистрации
REGISTRATION_START, REGISTRATION_INPUT, REGISTRATION_CONFIRM = range(3)


class RegistrationHandlers(BaseHandler):
    """
    Обработчики для процесса регистрации пользователей.
    
    Управляет пошаговым анкетированием через State Machine.
    """
    
    def __init__(self, registration_service: RegistrationService):
        """
        Инициализация обработчиков регистрации.
        
        Args:
            registration_service: Сервис регистрации
        """
        super().__init__(registration_service.client_service)
        self.registration_service = registration_service
        
        logger.info("RegistrationHandlers инициализирован")
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Заглушка для базового метода.
        
        Фактическая обработка происходит в специфичных методах.
        """
        pass
    
    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Начать процесс регистрации.
        """
        user_id, username, first_name = await self.get_user_info(update)
        
        logger.info(f"Команда start_registration от пользователя {first_name or 'Unknown'} (@{username}, ID: {user_id})")
        
        try:
            # Начинаем регистрацию
            registration = self.registration_service.start_registration(user_id, username)
            
            # Отправляем приветственное сообщение
            welcome_message = tpl.registration_welcome()
            
            # Отправляем приветственное сообщение
            if update.callback_query:
                # Если это callback_query, отправляем новое сообщение
                await update.callback_query.message.reply_text(welcome_message)
                # Переходим к первому вопросу
                await self._send_current_question_for_callback(update.callback_query.message, context, registration.current_state)
            else:
                # Если это обычное сообщение
                await update.message.reply_text(welcome_message)
                # Переходим к первому вопросу
                await self._send_current_question(update, context, registration.current_state)
            
            return REGISTRATION_INPUT
            
        except Exception as e:
            await self.handle_error(update, context, e)
            return ConversationHandler.END
    
    async def process_registration_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Обработать ввод пользователя в процессе регистрации.
        """
        user_id, username, first_name = await self.get_user_info(update)
        user_input = update.message.text
        
        logger.debug(f"Обработка ввода регистрации от пользователя {user_id}: '{user_input}'")
        
        try:
            # Проверяем, активна ли регистрация
            if not self.registration_service.is_registration_active(user_id):
                await update.message.reply_text(tpl.registration_not_found())
                return ConversationHandler.END
            
            # Обрабатываем специальные команды
            if user_input.lower() == '/cancel':
                await self._cancel_registration(update, context, user_id)
                return ConversationHandler.END
            
            # Обрабатываем ввод
            registration, step_completed = self.registration_service.process_input(user_id, user_input)
            
            if step_completed:
                # Переходим к следующему шагу
                if registration.current_state == RegistrationState.CONFIRMATION:
                    await self._show_confirmation(update, context, registration)
                    return REGISTRATION_CONFIRM
                else:
                    await self._send_current_question(update, context, registration.current_state)
                    return REGISTRATION_INPUT
            
            return REGISTRATION_INPUT
            
        except ValidationError as e:
            # Ошибка валидации - выводим только понятное сообщение без технических деталей
            try:
                # Берём текст первой ошибки Pydantic
                first_err = e.errors()[0]
                details = first_err.get("msg", "Неверное значение")
            except Exception:
                details = "Неверное значение"

            friendly_error = tpl.registration_validation_error(details)
            await update.message.reply_text(friendly_error)
            return REGISTRATION_INPUT
            
        except BusinessLogicError as e:
            # Ошибка бизнес-логики
            await update.message.reply_text(f"❌ {str(e)}")
            return ConversationHandler.END
            
        except Exception as e:
            await self.handle_error(update, context, e)
            return ConversationHandler.END
    
    async def confirm_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Подтвердить и завершить регистрацию.
        """
        user_id, username, first_name = await self.get_user_info(update)
        
        logger.info(f"Команда confirm_registration от пользователя {first_name or 'Unknown'} (@{username}, ID: {user_id})")
        
        try:
            # Завершаем регистрацию
            success = await self.registration_service.complete_registration(user_id)
            
            if success:
                success_message = tpl.registration_success()
                
                # Проверяем, это callback_query или обычное сообщение
                if update.callback_query:
                    await update.callback_query.edit_message_text(success_message)
                else:
                    await update.message.reply_text(success_message)
                return ConversationHandler.END
            else:
                if update.callback_query:
                    await update.callback_query.edit_message_text(tpl.generic_error())
                else:
                    await update.message.reply_text(tpl.generic_error())
                return REGISTRATION_CONFIRM
                
        except Exception as e:
            await self.handle_error(update, context, e)
            return ConversationHandler.END
    
    async def _send_current_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: RegistrationState) -> None:
        """
        Отправить текущий вопрос пользователю.
        
        Args:
            update: Telegram Update
            context: Telegram Context
            state: Текущее состояние регистрации
        """
        if state not in REGISTRATION_STEPS:
            await update.message.reply_text(tpl.registration_process_error())
            return
        
        step = REGISTRATION_STEPS[state]
        
        # Формируем сообщение
        message = f"{step.question}\n\n"
        if step.help_text:
            message += f"💡 {step.help_text}"
        
        reply_markup = tpl.options_keyboard(step.options) if step.options else None
        
        await update.message.reply_text(message, reply_markup=reply_markup)
    
    async def _show_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, registration) -> None:
        """
        Показать данные для подтверждения.
        
        Args:
            update: Telegram Update
            context: Telegram Context
            registration: Данные регистрации
        """
        summary = registration.get_summary()
        
        confirmation_message = tpl.registration_confirmation(summary)
        
        await update.message.reply_text(
            confirmation_message,
            reply_markup=tpl.registration_confirmation_keyboard(),
        )
    
    async def _cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """
        Отменить регистрацию.
        
        Args:
            update: Telegram Update
            context: Telegram Context
            user_id: ID пользователя
        """
        self.registration_service.cancel_registration(user_id)
        
        cancel_message = tpl.registration_cancelled()
        
        await update.message.reply_text(cancel_message)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Обработать нажатие инлайн кнопки.
        
        Args:
            update: Telegram Update
            context: Telegram Context
            
        Returns:
            Следующее состояние ConversationHandler
        """
        query = update.callback_query
        await query.answer()
        
        user_id, username, first_name = await self.get_user_info(update)
        
        callback_data = query.data
        
        try:
            # Обрабатываем кнопки подтверждения
            if callback_data == "confirm_yes":
                return await self.confirm_registration(update, context)
            elif callback_data == "confirm_edit":
                # Перезапускаем регистрацию
                self.registration_service.cancel_registration(user_id)
                await query.edit_message_text(tpl.registration_restart())
                return await self.start_registration(update, context)
            
            # Обрабатываем выбор опций регистрации
            elif callback_data.startswith("reg_"):
                selected_option = callback_data[4:]  # Убираем префикс "reg_"
                
                # Обрабатываем как обычный ввод
                registration, step_completed = self.registration_service.process_input(user_id, selected_option)
                
                if step_completed:
                    if registration.current_state == RegistrationState.CONFIRMATION:
                        await self._show_confirmation_callback(query, registration)
                        return REGISTRATION_CONFIRM
                    else:
                        await self._send_current_question_callback(query, registration.current_state)
                        return REGISTRATION_INPUT
                
                return REGISTRATION_INPUT
                
        except ValidationError as e:
            await query.edit_message_text(tpl.registration_validation_error(str(e)))
            return REGISTRATION_INPUT
            
        except Exception as e:
            await self.handle_error(update, context, e)
            return ConversationHandler.END
        
        return REGISTRATION_INPUT
    
    async def _send_current_question_callback(self, query, state: RegistrationState) -> None:
        """
        Отправить текущий вопрос через callback query.
        """
        if state not in REGISTRATION_STEPS:
            await query.edit_message_text(tpl.registration_process_error())
            return
        
        step = REGISTRATION_STEPS[state]
        
        # Формируем сообщение
        message = f"{step.question}\n\n"
        if step.help_text:
            message += f"💡 {step.help_text}"
        
        reply_markup = tpl.options_keyboard(step.options) if step.options else None
        
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    async def _show_confirmation_callback(self, query, registration) -> None:
        """
        Показать данные для подтверждения через callback query.
        """
        summary = registration.get_summary()
        
        confirmation_message = tpl.registration_confirmation(summary)
        
        await query.edit_message_text(
            confirmation_message,
            reply_markup=tpl.registration_confirmation_keyboard(),
        )
    
    async def _send_current_question_for_callback(self, message, context: ContextTypes.DEFAULT_TYPE, state: RegistrationState) -> None:
        """
        Отправить текущий вопрос через обычное сообщение (для callback).
        """
        if state not in REGISTRATION_STEPS:
            await message.reply_text(tpl.registration_process_error())
            return
        
        step = REGISTRATION_STEPS[state]
        
        # Формируем сообщение
        message_text = f"{step.question}\n\n"
        if step.help_text:
            message_text += f"💡 {step.help_text}"
        
        reply_markup = tpl.options_keyboard(step.options) if step.options else None
        
        await message.reply_text(message_text, reply_markup=reply_markup) 