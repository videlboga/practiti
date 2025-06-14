"""
📝 Сервис регистрации CyberKitty Practiti

Управляет процессом пошагового анкетирования новых пользователей.
"""

from typing import Dict, Optional
from ..models.registration import RegistrationData, RegistrationState, REGISTRATION_STEPS
from ..models.client import ClientCreateData
from ..services.protocols.client_service import ClientServiceProtocol
from ..utils.logger import get_logger
from ..utils.exceptions import ValidationError, BusinessLogicError

logger = get_logger(__name__)


class RegistrationService:
    """
    Сервис для управления процессом регистрации пользователей.
    
    Обеспечивает пошаговое анкетирование и валидацию данных.
    """
    
    def __init__(self, client_service: ClientServiceProtocol):
        """
        Инициализация сервиса регистрации.
        
        Args:
            client_service: Сервис для работы с клиентами
        """
        self.client_service = client_service
        self._active_registrations: Dict[int, RegistrationData] = {}
        
        logger.info("RegistrationService инициализирован")
    
    def start_registration(self, telegram_id: int, telegram_username: Optional[str] = None) -> RegistrationData:
        """
        Начать процесс регистрации для пользователя.
        
        Args:
            telegram_id: Telegram ID пользователя
            telegram_username: Telegram username пользователя
            
        Returns:
            Данные регистрации
        """
        logger.info(f"Начало регистрации для пользователя {telegram_id}")
        
        registration_data = RegistrationData(
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            current_state=RegistrationState.WAITING_NAME
        )
        
        self._active_registrations[telegram_id] = registration_data
        
        logger.debug(f"Регистрация создана для пользователя {telegram_id}")
        return registration_data
    
    def get_registration(self, telegram_id: int) -> Optional[RegistrationData]:
        """
        Получить данные регистрации пользователя.
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            Данные регистрации или None
        """
        return self._active_registrations.get(telegram_id)
    
    def is_registration_active(self, telegram_id: int) -> bool:
        """
        Проверить, активна ли регистрация для пользователя.
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            True если регистрация активна
        """
        registration = self.get_registration(telegram_id)
        return registration is not None and registration.current_state != RegistrationState.COMPLETED
    
    def process_input(self, telegram_id: int, user_input: str) -> tuple[RegistrationData, bool]:
        """
        Обработать ввод пользователя на текущем шаге регистрации.
        
        Args:
            telegram_id: Telegram ID пользователя
            user_input: Ввод пользователя
            
        Returns:
            Кортеж (обновленные данные регистрации, флаг завершения шага)
            
        Raises:
            ValidationError: При некорректном вводе
            BusinessLogicError: При ошибке бизнес-логики
        """
        registration = self.get_registration(telegram_id)
        if not registration:
            raise BusinessLogicError("Регистрация не найдена")
        
        logger.debug(f"Обработка ввода '{user_input}' для состояния {registration.current_state}")
        
        try:
            # Обрабатываем команду /skip
            if user_input.strip().lower() == '/skip':
                return self._handle_skip(registration)
            
            # Обрабатываем ввод в зависимости от текущего состояния
            if registration.current_state == RegistrationState.WAITING_NAME:
                return self._process_name(registration, user_input)
            elif registration.current_state == RegistrationState.WAITING_PHONE:
                return self._process_phone(registration, user_input)
            elif registration.current_state == RegistrationState.WAITING_AGE:
                return self._process_age(registration, user_input)
            elif registration.current_state == RegistrationState.WAITING_YOGA_EXPERIENCE:
                return self._process_yoga_experience(registration, user_input)
            elif registration.current_state == RegistrationState.WAITING_INTENSITY:
                return self._process_intensity(registration, user_input)
            elif registration.current_state == RegistrationState.WAITING_TIME_PREFERENCE:
                return self._process_time_preference(registration, user_input)
            elif registration.current_state == RegistrationState.WAITING_INJURIES:
                return self._process_injuries(registration, user_input)
            elif registration.current_state == RegistrationState.WAITING_GOALS:
                return self._process_goals(registration, user_input)
            elif registration.current_state == RegistrationState.WAITING_HOW_FOUND:
                return self._process_how_found(registration, user_input)
            else:
                raise BusinessLogicError(f"Неизвестное состояние: {registration.current_state}")
                
        except ValidationError:
            # Валидационные ошибки пробрасываем как есть
            raise
        except Exception as e:
            logger.error(f"Ошибка обработки ввода: {e}")
            raise BusinessLogicError(f"Ошибка обработки данных: {e}")
    
    def _handle_skip(self, registration: RegistrationData) -> tuple[RegistrationData, bool]:
        """Обработать команду /skip."""
        # Определяем, какие поля можно пропустить
        skippable_states = {
            RegistrationState.WAITING_AGE,
            RegistrationState.WAITING_INJURIES,
            RegistrationState.WAITING_GOALS,
            RegistrationState.WAITING_HOW_FOUND
        }
        
        if registration.current_state not in skippable_states:
            raise ValidationError("Этот шаг нельзя пропустить")
        
        # Переходим к следующему шагу
        next_state = self._get_next_state(registration.current_state)
        registration.current_state = next_state
        
        return registration, True
    
    def _process_name(self, registration: RegistrationData, name: str) -> tuple[RegistrationData, bool]:
        """Обработать ввод имени."""
        name = name.strip()
        if len(name) < 2:
            raise ValidationError("Имя должно содержать минимум 2 символа")
        if len(name) > 50:
            raise ValidationError("Имя не должно превышать 50 символов")
        
        registration.name = name
        registration.current_state = RegistrationState.WAITING_PHONE
        return registration, True
    
    def _process_phone(self, registration: RegistrationData, phone: str) -> tuple[RegistrationData, bool]:
        """Обработать ввод телефона."""
        try:
            # Используем валидатор из модели
            temp_data = RegistrationData(telegram_id=registration.telegram_id, phone=phone)
            registration.phone = temp_data.phone
            registration.current_state = RegistrationState.WAITING_AGE
            return registration, True
        except ValueError as e:
            raise ValidationError(str(e))
    
    def _process_age(self, registration: RegistrationData, age_str: str) -> tuple[RegistrationData, bool]:
        """Обработать ввод возраста."""
        try:
            age = int(age_str.strip())
            temp_data = RegistrationData(telegram_id=registration.telegram_id, age=age)
            registration.age = temp_data.age
            registration.current_state = RegistrationState.WAITING_YOGA_EXPERIENCE
            return registration, True
        except ValueError:
            raise ValidationError("Возраст должен быть числом от 16 до 80")
    
    def _process_yoga_experience(self, registration: RegistrationData, experience: str) -> tuple[RegistrationData, bool]:
        """Обработать ввод опыта йоги."""
        experience_lower = experience.lower().strip()
        if "да" in experience_lower or "есть" in experience_lower:
            registration.yoga_experience = True
        elif "нет" in experience_lower or "новичок" in experience_lower:
            registration.yoga_experience = False
        else:
            raise ValidationError("Пожалуйста, выберите 'Да, есть опыт' или 'Нет, я новичок'")
        
        registration.current_state = RegistrationState.WAITING_INTENSITY
        return registration, True
    
    def _process_intensity(self, registration: RegistrationData, intensity: str) -> tuple[RegistrationData, bool]:
        """Обработать ввод интенсивности."""
        intensity_lower = intensity.lower().strip()
        valid_intensities = {
            "низкая": "низкая",
            "средняя": "средняя", 
            "высокая": "высокая",
            "любая": "любая"
        }
        
        for key, value in valid_intensities.items():
            if key in intensity_lower:
                registration.intensity_preference = value
                registration.current_state = RegistrationState.WAITING_TIME_PREFERENCE
                return registration, True
        
        raise ValidationError("Пожалуйста, выберите: Низкая, Средняя, Высокая или Любая")
    
    def _process_time_preference(self, registration: RegistrationData, time_pref: str) -> tuple[RegistrationData, bool]:
        """Обработать ввод времени занятий."""
        time_lower = time_pref.lower().strip()
        
        if "утр" in time_lower:
            registration.time_preference = "утро"
        elif "дн" in time_lower:
            registration.time_preference = "день"
        elif "веч" in time_lower:
            registration.time_preference = "вечер"
        elif "люб" in time_lower:
            registration.time_preference = "любое"
        else:
            raise ValidationError("Пожалуйста, выберите: Утро, День, Вечер или Любое")
        
        registration.current_state = RegistrationState.WAITING_INJURIES
        return registration, True
    
    def _process_injuries(self, registration: RegistrationData, injuries: str) -> tuple[RegistrationData, bool]:
        """Обработать ввод травм/ограничений."""
        injuries = injuries.strip()
        if len(injuries) > 200:
            raise ValidationError("Описание травм не должно превышать 200 символов")
        
        registration.injuries = injuries if injuries else None
        registration.current_state = RegistrationState.WAITING_GOALS
        return registration, True
    
    def _process_goals(self, registration: RegistrationData, goals: str) -> tuple[RegistrationData, bool]:
        """Обработать ввод целей."""
        goals = goals.strip()
        if len(goals) > 200:
            raise ValidationError("Описание целей не должно превышать 200 символов")
        
        registration.goals = goals if goals else None
        registration.current_state = RegistrationState.WAITING_HOW_FOUND
        return registration, True
    
    def _process_how_found(self, registration: RegistrationData, how_found: str) -> tuple[RegistrationData, bool]:
        """Обработать ввод источника информации."""
        how_found = how_found.strip()
        if len(how_found) > 100:
            raise ValidationError("Ответ не должен превышать 100 символов")
        
        registration.how_found_us = how_found if how_found else None
        registration.current_state = RegistrationState.CONFIRMATION
        return registration, True
    
    def _get_next_state(self, current_state: RegistrationState) -> RegistrationState:
        """Получить следующее состояние."""
        state_order = [
            RegistrationState.WAITING_NAME,
            RegistrationState.WAITING_PHONE,
            RegistrationState.WAITING_AGE,
            RegistrationState.WAITING_YOGA_EXPERIENCE,
            RegistrationState.WAITING_INTENSITY,
            RegistrationState.WAITING_TIME_PREFERENCE,
            RegistrationState.WAITING_INJURIES,
            RegistrationState.WAITING_GOALS,
            RegistrationState.WAITING_HOW_FOUND,
            RegistrationState.CONFIRMATION
        ]
        
        try:
            current_index = state_order.index(current_state)
            if current_index < len(state_order) - 1:
                return state_order[current_index + 1]
            else:
                return RegistrationState.CONFIRMATION
        except ValueError:
            return RegistrationState.CONFIRMATION
    
    async def complete_registration(self, telegram_id: int) -> bool:
        """
        Завершить регистрацию и создать клиента.
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            True если регистрация успешно завершена
            
        Raises:
            BusinessLogicError: При ошибке завершения регистрации
        """
        registration = self.get_registration(telegram_id)
        if not registration:
            raise BusinessLogicError("Регистрация не найдена")
        
        if not registration.is_complete():
            raise BusinessLogicError("Регистрация не завершена - не все обязательные поля заполнены")
        
        try:
            # Создаем данные клиента
            client_data = ClientCreateData(
                name=registration.name,
                phone=registration.phone,
                telegram_id=registration.telegram_id,
                yoga_experience=registration.yoga_experience,
                intensity_preference=registration.intensity_preference,
                time_preference=registration.time_preference,
                age=registration.age,
                injuries=registration.injuries,
                goals=registration.goals,
                how_found_us=registration.how_found_us
            )
            
            # Создаем клиента через ClientService
            client = await self.client_service.create_client(client_data)
            
            # Помечаем регистрацию как завершенную
            registration.current_state = RegistrationState.COMPLETED
            
            # Удаляем из активных регистраций
            del self._active_registrations[telegram_id]
            
            logger.info(f"Регистрация пользователя {telegram_id} успешно завершена, создан клиент {client.id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка завершения регистрации для пользователя {telegram_id}: {e}")
            raise BusinessLogicError(f"Не удалось завершить регистрацию: {e}")
    
    def cancel_registration(self, telegram_id: int) -> bool:
        """
        Отменить регистрацию пользователя.
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            True если регистрация была отменена
        """
        if telegram_id in self._active_registrations:
            del self._active_registrations[telegram_id]
            logger.info(f"Регистрация пользователя {telegram_id} отменена")
            return True
        return False
    
    def get_current_step(self, telegram_id: int) -> Optional[dict]:
        """
        Получить информацию о текущем шаге регистрации.
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            Словарь с информацией о шаге или None
        """
        registration = self.get_registration(telegram_id)
        if not registration:
            return None
        
        if registration.current_state in REGISTRATION_STEPS:
            step = REGISTRATION_STEPS[registration.current_state]
            return {
                "question": step.question,
                "help_text": step.help_text,
                "options": step.options,
                "state": registration.current_state.value
            }
        
        return None
