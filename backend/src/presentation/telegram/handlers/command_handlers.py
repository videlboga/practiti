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
                    f"🌟 Добро пожаловать в Practiti!\n\n"
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
                "🧘‍♀️ **Practiti - Йога Студия**\n\n"
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

    async def clear_registration_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка команды /clear_registration.
        
        Очищает текущую регистрацию пользователя (для отладки).
        """
        await self.log_command(update, "clear_registration")
        
        try:
            user_id, username, _ = await self.get_user_info(update)
            
            # Получаем registration_service из application.bot_data
            bot_instance = context.application.bot_data.get('bot_instance')
            if bot_instance and hasattr(bot_instance, 'registration_service'):
                registration_service = bot_instance.registration_service
                
                # Очищаем ВСЕ регистрации (для отладки)
                count = registration_service.clear_all_registrations()
                
                message = f"✅ Очищено {count} активных регистраций. Можете начать заново с /register"
                logger.info(f"Очищено {count} активных регистраций по команде от @{username}")
            else:
                message = "❌ Ошибка доступа к сервису регистрации"
                logger.error("Не удалось получить registration_service")
            
            if update.effective_chat:
                await update.effective_chat.send_message(message)
                
        except Exception as e:
            await self.handle_error(update, context, e)

    async def address_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка команды /address.
        
        Показывает адрес студии и контактную информацию.
        """
        await self.log_command(update, "address")
        
        try:
            address_message = (
                "📍 **Адрес йога-студии Practiti:**\n\n"
                "🏢 **Основной зал:**\n"
                "г. Москва, ул. Примерная, д. 123\n"
                "м. Примерная (5 мин пешком)\n\n"
                "🕐 **Режим работы:**\n"
                "Пн-Пт: 07:00 - 22:00\n"
                "Сб-Вс: 09:00 - 20:00\n\n"
                "📞 **Контакты:**\n"
                "Телефон: +7 (999) 123-45-67\n"
                "WhatsApp: +7 (999) 123-45-67\n"
                "Email: info@practiti.ru\n\n"
                "🚇 **Как добраться:**\n"
                "• От м. Примерная - 5 мин пешком\n"
                "• Автобус: остановка 'Примерная улица'\n"
                "• Парковка: есть бесплатная\n\n"
                "🗺️ **Ориентиры:**\n"
                "Рядом с кафе 'Здоровье' и аптекой\n"
                "Вход со двора, 2 этаж\n\n"
                "💬 Есть вопросы? Напишите /contact"
            )
            
            if update.effective_chat:
                await update.effective_chat.send_message(address_message, parse_mode='Markdown')
                
            logger.info("Команда /address выполнена")
                
        except Exception as e:
            await self.handle_error(update, context, e)

    async def faq_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка команды /faq.
        
        Показывает часто задаваемые вопросы.
        """
        await self.log_command(update, "faq")
        
        try:
            faq_message = (
                "❓ **Часто задаваемые вопросы:**\n\n"
                "**🧘‍♀️ О занятиях:**\n\n"
                "**Q: Нужен ли опыт для занятий йогой?**\n"
                "A: Нет! У нас есть группы для начинающих. Каждый найдет подходящий уровень.\n\n"
                "**Q: Что взять с собой на первое занятие?**\n"
                "A: Удобную одежду, воду и хорошее настроение! Коврики предоставляем.\n\n"
                "**Q: Можно ли заниматься при травмах?**\n"
                "A: Обязательно сообщите инструктору о любых ограничениях. Мы адаптируем практику.\n\n"
                "**💳 Об абонементах:**\n\n"
                "**Q: Какие есть виды абонементов?**\n"
                "A: Разовые занятия, абонементы на 4, 8, 12 занятий. Подробности: /prices\n\n"
                "**Q: Сколько действует абонемент?**\n"
                "A: 4 занятия - 1 месяц, 8 занятий - 2 месяца, 12 занятий - 3 месяца.\n\n"
                "**Q: Можно ли заморозить абонемент?**\n"
                "A: Да, при болезни или отъезде. Обратитесь к администратору.\n\n"
                "**📅 О записи:**\n\n"
                "**Q: Как записаться на занятие?**\n"
                "A: Через этот бот командой /book или по телефону +7 (999) 123-45-67\n\n"
                "**Q: За сколько можно отменить запись?**\n"
                "A: За 4 часа до начала занятия без потери занятия с абонемента.\n\n"
                "**Q: Что если опоздал на занятие?**\n"
                "A: Можем пустить в первые 10 минут, но лучше приходить заранее.\n\n"
                "**🤔 Остались вопросы?**\n"
                "Напишите /contact или позвоните +7 (999) 123-45-67"
            )
            
            if update.effective_chat:
                await update.effective_chat.send_message(faq_message, parse_mode='Markdown')
                
            logger.info("Команда /faq выполнена")
                
        except Exception as e:
            await self.handle_error(update, context, e)

    async def contact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка команды /contact.
        
        Показывает контактную информацию для связи с администратором.
        """
        await self.log_command(update, "contact")
        
        try:
            contact_message = (
                "📞 **Связь с администратором:**\n\n"
                "👩‍💼 **Администратор студии:**\n"
                "Анна Петрова\n\n"
                "📱 **Основные контакты:**\n"
                "• Телефон: +7 (999) 123-45-67\n"
                "• WhatsApp: +7 (999) 123-45-67\n"
                "• Telegram: @practiti_admin\n"
                "• Email: info@practiti.ru\n\n"
                "🕐 **Время работы администратора:**\n"
                "Пн-Пт: 09:00 - 21:00\n"
                "Сб-Вс: 10:00 - 18:00\n\n"
                "⚡ **Быстрая помощь:**\n"
                "• Запись на занятие: /book\n"
                "• Вопросы о студии: /faq\n"
                "• Адрес и проезд: /address\n\n"
                "📝 **По каким вопросам обращаться:**\n"
                "• Покупка и продление абонементов\n"
                "• Заморозка абонемента\n"
                "• Индивидуальные занятия\n"
                "• Корпоративные программы\n"
                "• Мастер-классы и семинары\n"
                "• Технические проблемы с ботом\n\n"
                "💬 **Напишите нам в любое удобное время!**\n"
                "Мы ответим в рабочие часы."
            )
            
            if update.effective_chat:
                await update.effective_chat.send_message(contact_message, parse_mode='Markdown')
                
            logger.info("Команда /contact выполнена")
                
        except Exception as e:
            await self.handle_error(update, context, e)

    async def prices_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка команды /prices.
        
        Показывает цены на абонементы и услуги.
        """
        await self.log_command(update, "prices")
        
        try:
            prices_message = (
                "💰 **Цены на абонементы и услуги:**\n\n"
                "🎫 **Абонементы на групповые занятия:**\n\n"
                "• **Разовое занятие** - 1 500 ₽\n"
                "  Действует в день покупки\n\n"
                "• **Абонемент 4 занятия** - 5 200 ₽ (1 300 ₽/занятие)\n"
                "  Срок действия: 1 месяц\n"
                "  💡 Экономия: 800 ₽\n\n"
                "• **Абонемент 8 занятий** - 9 600 ₽ (1 200 ₽/занятие)\n"
                "  Срок действия: 2 месяца\n"
                "  💡 Экономия: 2 400 ₽\n\n"
                "• **Абонемент 12 занятий** - 13 200 ₽ (1 100 ₽/занятие)\n"
                "  Срок действия: 3 месяца\n"
                "  💡 Экономия: 4 800 ₽\n\n"
                "👤 **Индивидуальные занятия:**\n\n"
                "• **Персональное занятие** - 4 000 ₽\n"
                "  Продолжительность: 90 минут\n\n"
                "• **Парное занятие** - 3 000 ₽/чел\n"
                "  Продолжительность: 90 минут\n\n"
                "🎁 **Специальные предложения:**\n\n"
                "• **Первое занятие** - 1 000 ₽\n"
                "  Для новых клиентов\n\n"
                "• **Студенческая скидка** - 10%\n"
                "  При предъявлении студенческого\n\n"
                "• **Семейный абонемент** - скидка 15%\n"
                "  При покупке от 2-х абонементов\n\n"
                "💳 **Способы оплаты:**\n"
                "• Наличные в студии\n"
                "• Банковская карта\n"
                "• Перевод по номеру телефона\n"
                "• QR-код (СБП)\n\n"
                "📞 **Покупка абонементов:**\n"
                "Свяжитесь с администратором: /contact"
            )
            
            if update.effective_chat:
                await update.effective_chat.send_message(prices_message, parse_mode='Markdown')
                
            logger.info("Команда /prices выполнена")
                
        except Exception as e:
            await self.handle_error(update, context, e)

    async def schedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработка команды /schedule.
        
        Показывает расписание занятий на неделю.
        """
        await self.log_command(update, "schedule")
        
        try:
            schedule_message = (
                "📅 **Расписание занятий:**\n\n"
                "**🌅 ПОНЕДЕЛЬНИК:**\n"
                "• 08:00 - 09:30 | Хатха-йога (начинающие)\n"
                "• 19:00 - 20:30 | Виньяса-флоу (средний)\n"
                "• 20:45 - 22:00 | Йога-нидра (все уровни)\n\n"
                "**🌟 ВТОРНИК:**\n"
                "• 07:30 - 09:00 | Утренняя практика (все уровни)\n"
                "• 18:30 - 20:00 | Хатха-йога (средний)\n"
                "• 20:15 - 21:30 | Инь-йога (все уровни)\n\n"
                "**🔥 СРЕДА:**\n"
                "• 08:00 - 09:30 | Аштанга-йога (продвинутый)\n"
                "• 19:00 - 20:30 | Хатха-йога (начинающие)\n"
                "• 20:45 - 22:00 | Медитация (все уровни)\n\n"
                "**💫 ЧЕТВЕРГ:**\n"
                "• 07:30 - 09:00 | Виньяса-флоу (средний)\n"
                "• 18:30 - 20:00 | Хатха-йога (все уровни)\n"
                "• 20:15 - 21:30 | Восстановительная йога\n\n"
                "**🌸 ПЯТНИЦА:**\n"
                "• 08:00 - 09:30 | Хатха-йога (начинающие)\n"
                "• 19:00 - 20:30 | Виньяса-флоу (средний)\n"
                "• 20:45 - 22:00 | Йога-нидра (все уровни)\n\n"
                "**🧘‍♀️ СУББОТА:**\n"
                "• 10:00 - 11:30 | Семейная йога (все возрасты)\n"
                "• 12:00 - 13:30 | Хатха-йога (все уровни)\n"
                "• 14:00 - 15:30 | Мастер-класс (тема меняется)\n\n"
                "**🌅 ВОСКРЕСЕНЬЕ:**\n"
                "• 10:00 - 11:30 | Утренняя практика (все уровни)\n"
                "• 12:00 - 13:30 | Инь-йога (все уровни)\n"
                "• 14:00 - 15:30 | Медитация и пранаяма\n\n"
                "**📝 Уровни сложности:**\n"
                "🟢 Начинающие - без опыта\n"
                "🟡 Средний - от 6 месяцев практики\n"
                "🔴 Продвинутый - от 2 лет практики\n\n"
                "**📞 Запись на занятия:**\n"
                "• Через бот: /book (для зарегистрированных)\n"
                "• По телефону: +7 (999) 123-45-67\n"
                "• В студии у администратора\n\n"
                "⚠️ **Важно:** Запись обязательна!\n"
                "Отмена за 4 часа до занятия."
            )
            
            if update.effective_chat:
                await update.effective_chat.send_message(schedule_message, parse_mode='Markdown')
                
            logger.info("Команда /schedule выполнена")
                
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