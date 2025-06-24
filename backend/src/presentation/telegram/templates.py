from __future__ import annotations

"""📨 Шаблоны сообщений и клавиатур для Telegram-бота Practiti.

Все текстовые константы собраны в одном месте, чтобы:
1. Избежать дублирования строк в хендлерах.
2. Проще поддерживать локализацию и изменение wording.
3. Обеспечить единый стиль сообщений (эмодзи, форматирование, ссылки).

Каждая функция возвращает готовую строку либо объект `InlineKeyboardMarkup`.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

__all__ = [
    # Сообщения
    "welcome_back",
    "welcome_new",
    "help_registered",
    "help_unregistered",
    "info_message",
    "registration_intro",
    "unknown_command_message",
    # Клавиатуры
    "registration_keyboard",
    "options_keyboard",
    "registration_confirmation_keyboard",
    # Бронирования
    "booking_prompt",
    "booking_not_registered",
    "booking_invalid_format",
    "booking_invalid_datetime",
    "booking_success",
    "booking_cancelled",
    "booking_failure",
    # Регистрация
    "registration_welcome",
    "registration_confirmation",
    "registration_success",
    "registration_cancelled",
    "registration_restart",
    "registration_process_error",
    "registration_not_found",
    "registration_validation_error",
    # Общие
    "generic_error",
    "feature_unavailable",
    # Тест уведомлений
    "test_notification_message",
    "test_notification_sent",
    "test_notification_failed",
]

# ------------------------
# Сообщения
# ------------------------

def welcome_back(client_name: str) -> str:
    """Приветствие для уже зарегистрированного клиента."""
    return (
        f"👋 Добро пожаловать обратно, {client_name}!\n\n"
        f"🧘‍♀️ Вы зарегистрированы в йога-студии\n\n"
        f"📋 Используйте /help для просмотра доступных команд"
    )


def welcome_new(first_name: str | None) -> str:
    """Приветствие для нового пользователя."""
    return (
        "🌟 Добро пожаловать в Practiti!\n\n"
        f"👋 Привет, {first_name or 'друг'}!\n\n"
        "📝 Для записи на занятия нужно пройти регистрацию.\n"
        "Это займет всего пару минут!\n\n"
        "🔹 /register - начать регистрацию\n"
        "🔹 /help - посмотреть все команды\n"
        "🔹 /info - узнать о студии"
    )


def help_registered() -> str:
    """/help для зарегистрированного пользователя."""
    return (
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


def help_unregistered() -> str:
    """/help для незарегистрированного пользователя."""
    return (
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


def info_message() -> str:
    """Сообщение /info о студии."""
    return (
        "🧘‍♀️ **Practiti - Йога Студия**\n\n"
        "✨ **Наша миссия:**\n"
        "Создать пространство гармонии, где каждый может найти свой путь к внутреннему равновесию через практику йоги.\n\n"
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


def registration_intro() -> str:
    """Первое сообщение при запуске регистрации."""
    return (
        "📝 **Начинаем регистрацию!**\n\n"
        "Процесс займет всего 2-3 минуты.\n"
        "Я задам несколько вопросов, чтобы подобрать идеальные занятия для вас.\n\n"
        "⏭️ Некоторые вопросы можно пропустить командой /skip\n"
        "❌ Отменить регистрацию: /cancel\n\n"
        "Готовы начать? 🚀"
    )


def unknown_command_message() -> str:
    """Ответ на неизвестную команду."""
    return (
        "🤔 Команда не найдена.\n\n"
        "📋 Используйте /help для просмотра всех доступных команд.\n\n"
        "💡 Возможно, вы имели в виду:\n"
        "• /start - главное меню\n"
        "• /info - о студии\n"
        "• /register - регистрация"
    )

# ------------------------
# Клавиатуры
# ------------------------

def registration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопками начать/отменить регистрацию."""
    keyboard = [
        [InlineKeyboardButton("🚀 Начать регистрацию", callback_data="start_registration")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_registration")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ------------------------
# Клавиатуры – фабрики
# ------------------------

def options_keyboard(options: list[str], prefix: str = "reg_") -> InlineKeyboardMarkup:
    """Сгенерировать Inline-клавиатуру из списка вариантов.

    Args:
        options: Список строк для кнопок.
        prefix: Префикс, который будет добавлен к callback_data.

    Returns:
        InlineKeyboardMarkup со столбцом кнопок.
    """

    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(opt, callback_data=f"{prefix}{opt}")]
         for opt in options]
    )

def registration_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения данных регистрации."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes")],
            [InlineKeyboardButton("✏️ Изменить", callback_data="confirm_edit")],
        ]
    )

# ------------------------
# Бронирования
# ------------------------

def booking_prompt() -> str:
    """Сообщение-подсказка для ввода даты/времени/типа класса."""
    return (
        "📅 Введите *дату*, *время* и *тип* занятия через пробел.\n\n"
        "Формат: `YYYY-MM-DD HH:MM тип`\n"
        "Пример: `2025-07-01 19:00 хатха`"
    )


def booking_not_registered() -> str:
    """Сообщение, если пользователь пытается бронировать без регистрации."""
    return (
        "📝 Сначала пройдите регистрацию в студии.\n"
        "Используйте /register, это займёт пару минут."
    )


def booking_invalid_format() -> str:
    """Ошибка, если строка не содержит три части."""
    return "❌ Неверный формат. Попробуйте ещё раз или /cancel."


def booking_invalid_datetime() -> str:
    """Ошибка, если дата/время не разобрались."""
    return "❌ Не удалось разобрать дату/время. Используйте формат YYYY-MM-DD HH:MM."


def booking_success(dt: datetime) -> str:  # type: ignore[name-defined]
    """Успешное бронирование."""
    from datetime import datetime as _dt  # локальный импорт, чтобы избежать циклов

    if isinstance(dt, _dt):
        formatted = dt.strftime("%d.%m %H:%M")
    else:
        formatted = str(dt)
    return f"✅ Запись создана! До встречи {formatted} ✨"


def booking_cancelled() -> str:
    """Сообщение при отмене брони (диалога)."""
    return "❌ Запись отменена."


def booking_failure(reason: str | None = None) -> str:
    """Сообщение при неудачном создании брони."""
    base = "🚫 Не удалось создать запись."
    if reason:
        return f"{base}\n{reason}"
    return base

# ------------------------
# Регистрация
# ------------------------

def registration_welcome() -> str:
    """Приветственное сообщение при запуске регистрации."""
    return (
        "🌟 **Добро пожаловать в йога-студию!**\n\n"
        "Давайте познакомимся! Я задам вам несколько вопросов, чтобы подобрать идеальные занятия йогой.\n\n"
        "📝 Процесс займет всего 2-3 минуты\n"
        "⏭️ Некоторые вопросы можно пропустить командой /skip\n"
        "❌ Отменить регистрацию: /cancel\n\n"
        "Готовы начать? 🚀"
    )


def registration_confirmation(summary: str) -> str:
    """Сообщение подтверждения регистрации с резюме."""
    return (
        f"{summary}\n\n"
        "✅ **Все верно?**\n\n"
        "Если данные корректны, нажмите \"Подтвердить\".\n"
        "Если нужно что-то изменить, нажмите \"Изменить\"."
    )


def registration_success() -> str:
    """Сообщение об успешном завершении регистрации."""
    return (
        "🎉 **Регистрация завершена!**\n\n"
        "Добро пожаловать в нашу йога-студию! \n\n"
        "✅ Ваши данные сохранены\n"
        "📱 Теперь вы можете записываться на занятия\n"
        "💬 Используйте /help для просмотра доступных команд\n\n"
        "Намасте! 🙏"
    )


def registration_cancelled() -> str:
    """Сообщение при отмене регистрации пользователем."""
    return (
        "❌ **Регистрация отменена**\n\n"
        "Если передумаете, просто напишите /start снова.\n\n"
        "До встречи! 👋"
    )


def registration_restart() -> str:
    """Сообщение о перезапуске регистрации."""
    return "🔄 Начинаем регистрацию заново..."


def registration_process_error() -> str:
    """Ошибка процесса регистрации."""
    return "❌ Ошибка в процессе регистрации"


def registration_not_found() -> str:
    """Регистрация не найдена/прервана."""
    return "❌ Регистрация не найдена. Начните заново с команды /start"


def registration_validation_error(details: str) -> str:
    """Форматировать сообщение об ошибке валидации."""
    return (
        f"⚠️ {details}\n"
        "Пожалуйста, попробуйте ещё раз или отправьте /cancel для выхода."
    )

# ------------------------
# Общие ошибки / статусы
# ------------------------

def generic_error() -> str:
    """Непредвиденная ошибка."""
    return "🚫 Произошла ошибка. Попробуйте позже."

def feature_unavailable() -> str:
    """Функциональность временно выключена."""
    return "🚧 Функция временно недоступна. Попробуйте позже."

# ------------------------
# Тест уведомлений
# ------------------------

def test_notification_message() -> str:
    """Содержимое тестового уведомления пользователю."""
    return "🔔 Это тестовое уведомление. Всё работает! ✅"

def test_notification_sent() -> str:
    """Ответ, когда тестовое уведомление успешно отправлено."""
    return "✅ Тестовое уведомление отправлено."

def test_notification_failed() -> str:
    """Ответ, когда тестовое уведомление не удалось отправить."""
    return "⚠️ Не удалось отправить уведомление. Проверьте логи сервера." 