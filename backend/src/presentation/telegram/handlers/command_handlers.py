"""
📋 Обработчики команд Telegram Bot

Основные команды: /start, /help и другие.
Принцип CyberKitty: простота превыше всего.
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from .base_handler import BaseHandler
from ....services.protocols.client_service import ClientServiceProtocol

logger = logging.getLogger(__name__)


class CommandHandlers(BaseHandler):
    """
    Обработчик основных команд бота.
    
    Обрабатывает:
    - /start - приветствие и регистрация
    - /help - справка по командам
    """
    
    def __init__(self, client_service: ClientServiceProtocol):
        """
        Инициализация обработчика команд.
        
        Args:
            client_service: Сервис для работы с клиентами
        """
        super().__init__(client_service)
        logger.info("CommandHandlers инициализирован")
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Заглушка для базового метода.
        
        Фактическая обработка происходит в специфичных методах.
        """
        pass
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка команды /start.
        
        Приветствует пользователя и предлагает пройти регистрацию.
        """
        await self.log_command(update, "start")
        
        try:
            user_id, username, first_name = await self.get_user_info(update)
            
            # Проверяем, зарегистрирован ли пользователь
            existing_client = await self.client_service.get_client_by_telegram_id(user_id)
            
            if existing_client:
                # Пользователь уже зарегистрирован
                welcome_message = (
                    f"👋 Добро пожаловать обратно, {existing_client.name}!\n\n"
                    f"🧘‍♀️ Вы зарегистрированы в йога-студии\n\n"
                    f"📋 Используйте /help для просмотра доступных команд"
                )
                
                logger.info(f"Команда /start: существующий клиент {existing_client.name}")
            else:
                # Новый пользователь
                welcome_message = (
                    f"🌟 Добро пожаловать в йога-студию!\n\n"
                    f"👋 Привет, {first_name or 'друг'}!\n\n"
                    f"📝 Для записи на занятия нужно пройти регистрацию.\n"
                    f"Это займет всего пару минут!\n\n"
                    f"🔹 /register - начать регистрацию\n"
                    f"🔹 /help - посмотреть все команды\n"
                    f"🔹 /info - узнать о студии"
                )
                
                logger.info(f"Команда /start: новый пользователь @{username}")
            
            if update.effective_chat:
                await update.effective_chat.send_message(welcome_message)
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка команды /help.
        
        Показывает список доступных команд.
        """
        await self.log_command(update, "help")
        
        try:
            user_id, _, _ = await self.get_user_info(update)
            
            # Проверяем статус пользователя
            existing_client = await self.client_service.get_client_by_telegram_id(user_id)
            
            if existing_client:
                # Команды для зарегистрированного пользователя
                help_message = (
                    "📋 **Доступные команды:**\n\n"
                    "🔹 **Основные:**\n"
                    "/start - главное меню\n"
                    "/help - эта справка\n"
                    "/info - информация о студии\n\n"
                    "🔹 **Мой профиль:**\n"
                    "/profile - мои данные\n"
                    "/subscriptions - мои абонементы\n"
                    "/classes - записи на занятия\n\n"
                    "🔹 **Занятия:**\n"
                    "/schedule - расписание\n"
                    "/book - записаться на занятие\n\n"
                    "🔹 **Поддержка:**\n"
                    "/contact - связь с администратором\n"
                    "/faq - часто задаваемые вопросы\n\n"
                    "✨ Ваш путь к гармонии! 🧘‍♀️"
                )
                
                logger.info(f"Команда /help: зарегистрированный клиент {existing_client.name}")
            else:
                # Команды для незарегистрированного пользователя
                help_message = (
                    "📋 **Доступные команды:**\n\n"
                    "🔹 **Для начала:**\n"
                    "/start - главное меню\n"
                    "/register - пройти регистрацию\n"
                    "/help - эта справка\n\n"
                    "🔹 **Информация:**\n"
                    "/info - о студии\n"
                    "/address - адрес и контакты\n"
                    "/prices - цены на абонементы\n"
                    "/schedule - расписание занятий\n\n"
                    "🔹 **Поддержка:**\n"
                    "/contact - связь с администратором\n"
                    "/faq - часто задаваемые вопросы\n\n"
                    "📝 **Для записи на занятия необходима регистрация!**\n\n"
                    "✨ Просто начните! 🌟"
                )
                
                logger.info("Команда /help: незарегистрированный пользователь")
            
            if update.effective_chat:
                await update.effective_chat.send_message(help_message, parse_mode='Markdown')
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка команды /info.
        
        Показывает информацию о студии.
        """
        await self.log_command(update, "info")
        
        try:
            info_message = (
                "🧘‍♀️ **Йога Студия**\n\n"
                "✨ **Наша миссия:**\n"
                "Создать пространство гармонии, где каждый может найти "
                "свой путь к внутреннему равновесию через практику йоги.\n\n"
                "🌟 **Наши принципы:**\n"
                "• Индивидуальный подход к каждому\n"
                "• Атмосфера принятия и поддержки\n"
                "• Качественное обучение\n\n"
                "🔹 **Что мы предлагаем:**\n"
                "• Хатха-йога для всех уровней\n"
                "• Виньяса-флоу\n"
                "• Йога для начинающих\n"
                "• Индивидуальные занятия\n"
                "• Мастер-классы и семинары\n\n"
                "📞 **Контакты:**\n"
                "/address - адрес студии\n"
                "/contact - связь с нами\n\n"
                "💚 Добро пожаловать в мир йоги!"
            )
            
            if update.effective_chat:
                await update.effective_chat.send_message(info_message, parse_mode='Markdown')
                
            logger.info("Команда /info выполнена")
                
        except Exception as e:
            await self.handle_error(update, context, e)
    
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка команды /register.
        
        Начинает процесс регистрации нового пользователя.
        """
        await self.log_command(update, "register")
        
        try:
            user_id, username, first_name = await self.get_user_info(update)
            
            # Проверяем, не зарегистрирован ли уже пользователь
            existing_client = await self.client_service.get_client_by_telegram_id(user_id)
            
            if existing_client:
                # Пользователь уже зарегистрирован
                already_registered_message = (
                    f"✅ {existing_client.name}, вы уже зарегистрированы!\n\n"
                    f"📋 Используйте /help для просмотра доступных команд\n"
                    f"🧘‍♀️ Или /schedule для просмотра расписания занятий"
                )
                
                if update.effective_chat:
                    await update.effective_chat.send_message(already_registered_message)
                    
                logger.info(f"Команда /register: пользователь {existing_client.name} уже зарегистрирован")
            else:
                # Новый пользователь - перенаправляем к registration handlers
                # Здесь будет интеграция с RegistrationHandlers
                register_message = (
                    "📝 **Начинаем регистрацию!**\n\n"
                    "Процесс займет всего 2-3 минуты.\n"
                    "Я задам несколько вопросов, чтобы подобрать идеальные занятия для вас.\n\n"
                    "⏭️ Некоторые вопросы можно пропустить командой /skip\n"
                    "❌ Отменить регистрацию: /cancel\n\n"
                    "Готовы начать? 🚀"
                )
                
                # Создаем инлайн кнопки
                keyboard = [
                    [InlineKeyboardButton("🚀 Начать регистрацию", callback_data="start_registration")],
                    [InlineKeyboardButton("❌ Отменить", callback_data="cancel_registration")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if update.effective_chat:
                    await update.effective_chat.send_message(
                        register_message, 
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                
                # TODO: Здесь будет вызов RegistrationHandlers.start_registration()
                logger.info(f"Команда /register: начало регистрации для @{username}")
                
        except Exception as e:
            await self.handle_error(update, context, e)

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка неизвестных команд.
        
        Подсказывает пользователю доступные команды.
        """
        try:
            user_id, username, _ = await self.get_user_info(update)
            logger.info(f"Неизвестная команда от @{username} (ID: {user_id}): {update.message.text}")
            
            unknown_message = (
                "🤔 Команда не найдена.\n\n"
                "📋 Используйте /help для просмотра всех доступных команд.\n\n"
                "💡 Возможно, вы имели в виду:\n"
                "• /start - главное меню\n"
                "• /info - о студии\n"
                "• /register - регистрация"
            )
            
            if update.effective_chat:
                await update.effective_chat.send_message(unknown_message)
                
        except Exception as e:
            await self.handle_error(update, context, e) 