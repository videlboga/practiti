"""
🎫 Сервис управления абонементами Practiti

Бизнес-логика для работы с абонементами клиентов йога-студии.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from ..models.subscription import (
    Subscription, SubscriptionCreateData, SubscriptionUpdateData, 
    SubscriptionType, SubscriptionStatus
)
from ..repositories.protocols.subscription_repository import SubscriptionRepositoryProtocol
from ..services.protocols.subscription_service import SubscriptionServiceProtocol
from ..utils.exceptions import BusinessLogicError
from ..utils.exceptions import ValidationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionService(SubscriptionServiceProtocol):
    """
    Сервис для управления абонементами клиентов.
    
    Реализует всю бизнес-логику работы с абонементами.
    """
    
    def __init__(self, subscription_repository: SubscriptionRepositoryProtocol):
        """
        Инициализация сервиса.
        
        Args:
            subscription_repository: Репозиторий для работы с данными абонементов
        """
        self._repository = subscription_repository
        logger.info("SubscriptionService инициализирован")
    
    async def create_subscription(self, data: SubscriptionCreateData) -> Subscription:
        """
        Создать новый абонемент.
        
        Args:
            data: Данные для создания абонемента
            
        Returns:
            Созданный абонемент
            
        Raises:
            BusinessLogicError: При нарушении бизнес-правил
        """
        logger.info(f"Создание абонемента {data.type.value} для клиента {data.client_id}")
        
        # Создаем абонемент через репозиторий (допускаем несколько активных)
        subscription = await self._repository.save_subscription(data)
        
        logger.info(f"Абонемент {subscription.id} создан успешно")
        return subscription
    
    async def get_subscription(self, subscription_id: str) -> Subscription:
        """
        Получить абонемент по ID.
        
        Args:
            subscription_id: ID абонемента
            
        Returns:
            Абонемент
            
        Raises:
            BusinessLogicError: Если абонемент не найден
        """
        subscription = await self._repository.get_subscription_by_id(subscription_id)
        if not subscription:
            raise BusinessLogicError(f"Абонемент с ID {subscription_id} не найден")
        
        return subscription
    
    async def get_all_subscriptions(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Subscription]:
        """
        Получить все абонементы.
        
        Args:
            limit: Максимальное количество абонементов
            offset: Смещение для пагинации
            
        Returns:
            Список всех абонементов
        """
        return await self._repository.list_subscriptions(limit=limit, offset=offset)
    
    async def get_client_subscriptions(self, client_id: str) -> List[Subscription]:
        """
        Получить все абонементы клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Список абонементов клиента
        """
        return await self._repository.get_subscriptions_by_client_id(client_id)
    
    async def get_subscriptions_by_status(self, status: SubscriptionStatus) -> List[Subscription]:
        """
        Получить абонементы по статусу.
        
        Args:
            status: Статус абонементов
            
        Returns:
            Список абонементов с указанным статусом
        """
        return await self._repository.get_subscriptions_by_status(status)
    
    async def get_active_subscription(self, client_id: str) -> Optional[Subscription]:
        """
        Получить активный абонемент клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Активный абонемент или None
        """
        active_subscriptions = await self._repository.get_active_subscriptions_by_client_id(client_id)
        
        # Фильтруем по реальной активности (с учетом дат и занятий)
        truly_active = [sub for sub in active_subscriptions if sub.is_active]
        
        if not truly_active:
            return None
        
        # Если несколько активных (не должно быть), возвращаем последний
        return max(truly_active, key=lambda x: x.created_at)
    
    async def use_class(self, subscription_id: str) -> Subscription:
        """
        Списать одно занятие с абонемента.
        
        Args:
            subscription_id: ID абонемента
            
        Returns:
            Обновленный абонемент
            
        Raises:
            BusinessLogicError: Если нельзя списать занятие
        """
        subscription = await self.get_subscription(subscription_id)
        
        # Проверяем, можно ли списать занятие
        if not subscription.is_active:
            raise BusinessLogicError(
                f"Абонемент {subscription_id} неактивен (статус: {subscription.status.value})"
            )
        
        remaining = subscription.remaining_classes
        if remaining is None:
            remaining = subscription.total_classes - subscription.used_classes
        if remaining <= 0:
            raise BusinessLogicError(
                f"На абонементе {subscription_id} закончились занятия"
            )
        
        # Списываем занятие
        new_used_classes = subscription.used_classes + 1
        remaining_after = subscription.remaining_classes - 1 if subscription.remaining_classes is not None else None
        update_data = SubscriptionUpdateData(
            used_classes=new_used_classes,
        )
        # Если можем вычислить оставшиеся, передадим в обновление (для репозитория, который хранит это поле)
        if remaining_after is not None:
            update_data_dict = update_data.model_dump(exclude_unset=True)
            update_data_dict["used_classes"] = new_used_classes
            update_data_dict["remaining_classes"] = remaining_after
            update_data = SubscriptionUpdateData(**update_data_dict)
        
        # Проверяем, не исчерпался ли абонемент
        if subscription.type != SubscriptionType.UNLIMITED and new_used_classes >= subscription.total_classes:
            update_data.status = SubscriptionStatus.EXHAUSTED
        
        updated_subscription = await self._repository.update_subscription(subscription_id, update_data)
        if not updated_subscription:
            raise BusinessLogicError(f"Не удалось обновить абонемент {subscription_id}")
        
        logger.info(f"Списано занятие с абонемента {subscription_id}. Осталось: {updated_subscription.remaining_classes}")
        return updated_subscription
    
    async def confirm_payment(self, subscription_id: str) -> Subscription:
        """
        Подтвердить оплату абонемента.
        
        Args:
            subscription_id: ID абонемента
            
        Returns:
            Обновленный абонемент
        """
        subscription = await self.get_subscription(subscription_id)
        
        if subscription.payment_confirmed:
            logger.warning(f"Оплата абонемента {subscription_id} уже подтверждена")
            return subscription
        
        # Подтверждаем оплату и активируем абонемент
        update_data = SubscriptionUpdateData(
            payment_confirmed=True,
            status=SubscriptionStatus.ACTIVE
        )
        
        updated_subscription = await self._repository.update_subscription(subscription_id, update_data)
        if not updated_subscription:
            raise BusinessLogicError(f"Не удалось обновить абонемент {subscription_id}")
        
        logger.info(f"Оплата абонемента {subscription_id} подтверждена")
        return updated_subscription
    
    async def extend_subscription(self, subscription_id: str, additional_days: int) -> Subscription:
        """
        Продлить срок действия абонемента.
        
        Args:
            subscription_id: ID абонемента
            additional_days: Количество дней для продления
            
        Returns:
            Обновленный абонемент
        """
        if additional_days <= 0:
            raise BusinessLogicError("Количество дней для продления должно быть положительным")
        
        subscription = await self.get_subscription(subscription_id)
        
        # Продлеваем дату окончания
        new_end_date = subscription.end_date + timedelta(days=additional_days)
        update_data = SubscriptionUpdateData(end_date=new_end_date)
        
        # Если абонемент был истекшим, делаем его активным
        if subscription.status == SubscriptionStatus.EXPIRED:
            update_data.status = SubscriptionStatus.ACTIVE
        
        updated_subscription = await self._repository.update_subscription(subscription_id, update_data)
        if not updated_subscription:
            raise BusinessLogicError(f"Не удалось обновить абонемент {subscription_id}")
        
        logger.info(f"Абонемент {subscription_id} продлен на {additional_days} дней до {new_end_date}")
        return updated_subscription
    
    async def suspend_subscription(self, subscription_id: str) -> Subscription:
        """
        Приостановить абонемент.
        
        Args:
            subscription_id: ID абонемента
            
        Returns:
            Обновленный абонемент
        """
        subscription = await self.get_subscription(subscription_id)
        
        if subscription.status == SubscriptionStatus.SUSPENDED:
            logger.warning(f"Абонемент {subscription_id} уже приостановлен")
            return subscription
        
        if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.PENDING]:
            raise BusinessLogicError(
                f"Нельзя приостановить абонемент со статусом {subscription.status.value}"
            )
        
        update_data = SubscriptionUpdateData(status=SubscriptionStatus.SUSPENDED)
        updated_subscription = await self._repository.update_subscription(subscription_id, update_data)
        
        if not updated_subscription:
            raise BusinessLogicError(f"Не удалось обновить абонемент {subscription_id}")
        
        logger.info(f"Абонемент {subscription_id} приостановлен")
        return updated_subscription
    
    async def resume_subscription(self, subscription_id: str) -> Subscription:
        """
        Возобновить приостановленный абонемент.
        
        Args:
            subscription_id: ID абонемента
            
        Returns:
            Обновленный абонемент
        """
        subscription = await self.get_subscription(subscription_id)
        
        if subscription.status != SubscriptionStatus.SUSPENDED:
            raise BusinessLogicError(
                f"Можно возобновить только приостановленный абонемент. Текущий статус: {subscription.status.value}"
            )
        
        # Определяем новый статус
        new_status = SubscriptionStatus.ACTIVE if subscription.payment_confirmed else SubscriptionStatus.PENDING
        
        update_data = SubscriptionUpdateData(status=new_status)
        updated_subscription = await self._repository.update_subscription(subscription_id, update_data)
        
        if not updated_subscription:
            raise BusinessLogicError(f"Не удалось обновить абонемент {subscription_id}")
        
        logger.info(f"Абонемент {subscription_id} возобновлен со статусом {new_status.value}")
        return updated_subscription
    
    async def update_subscription_status(self) -> int:
        """
        Обновить статусы всех абонементов (expired, exhausted).
        
        Проверяет все абонементы и обновляет их статусы согласно
        текущей дате и количеству оставшихся занятий.
        
        Returns:
            Количество обновленных абонементов
        """
        logger.info("Начинаем обновление статусов абонементов")
        
        # Получаем все активные абонементы
        active_subscriptions = await self._repository.get_subscriptions_by_status(SubscriptionStatus.ACTIVE)
        updated_count = 0
        
        today = date.today()
        
        for subscription in active_subscriptions:
            update_data = None
            
            # Проверяем истечение по дате
            if subscription.is_expired:
                update_data = SubscriptionUpdateData(status=SubscriptionStatus.EXPIRED)
                logger.info(f"Абонемент {subscription.id} истек по дате")
            
            # Проверяем исчерпание занятий
            elif subscription.is_exhausted:
                update_data = SubscriptionUpdateData(status=SubscriptionStatus.EXHAUSTED)
                logger.info(f"Абонемент {subscription.id} исчерпан")
            
            # Обновляем статус если нужно
            if update_data:
                await self._repository.update_subscription(subscription.id, update_data)
                updated_count += 1
        
        logger.info(f"Обновлено статусов абонементов: {updated_count}")
        return updated_count
    
    async def get_subscription_statistics(self, client_id: str) -> dict:
        """
        Получить статистику по абонементам клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Словарь со статистикой
        """
        subscriptions = await self.get_client_subscriptions(client_id)
        
        if not subscriptions:
            return {
                "total_subscriptions": 0,
                "active_subscriptions": 0,
                "total_classes_bought": 0,
                "total_classes_used": 0,
                "total_money_spent": 0,
                "favorite_subscription_type": None,
                "current_subscription": None
            }
        
        # Подсчитываем статистику
        total_subscriptions = len(subscriptions)
        active_subscriptions = len([s for s in subscriptions if s.is_active])
        total_classes_bought = sum(s.total_classes for s in subscriptions if s.type != SubscriptionType.UNLIMITED)
        total_classes_used = sum(s.used_classes for s in subscriptions)
        total_money_spent = sum(s.price for s in subscriptions if s.payment_confirmed)
        
        # Находим любимый тип абонемента
        type_counts = {}
        for subscription in subscriptions:
            type_counts[subscription.type] = type_counts.get(subscription.type, 0) + 1
        
        favorite_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
        
        # Текущий активный абонемент
        current_subscription = await self.get_active_subscription(client_id)
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "total_classes_bought": total_classes_bought,
            "total_classes_used": total_classes_used,
            "total_money_spent": total_money_spent,
            "favorite_subscription_type": favorite_type.value if favorite_type else None,
            "current_subscription": {
                "id": current_subscription.id,
                "type": current_subscription.type.value,
                "remaining_classes": current_subscription.remaining_classes,
                "end_date": current_subscription.end_date.isoformat()
                         } if current_subscription else None
        }
    
    def get_subscription_price(self, subscription_type: SubscriptionType) -> int:
        """
        Получить цену абонемента по типу.
        
        Args:
            subscription_type: Тип абонемента
            
        Returns:
            Цена в рублях
        """
        prices = {
            SubscriptionType.TRIAL: 500,
            SubscriptionType.SINGLE: 1100,
            SubscriptionType.PACKAGE_4: 3200,
            SubscriptionType.PACKAGE_8: 7000,
            SubscriptionType.PACKAGE_12: 9000,
            SubscriptionType.UNLIMITED: 10800,
        }
        return prices[subscription_type]
    
    def calculate_subscription_end_date(self, subscription_type: SubscriptionType, start_date: date) -> date:
        """
        Рассчитать дату окончания абонемента.
        
        Args:
            subscription_type: Тип абонемента
            start_date: Дата начала
            
        Returns:
            Дата окончания
        """
        if subscription_type == SubscriptionType.TRIAL:
            return start_date + timedelta(days=14)  # Пробный - 14 дней
        elif subscription_type == SubscriptionType.SINGLE:
            return start_date + timedelta(days=1)   # Разовое - 1 день
        else:
            return start_date + timedelta(days=30)  # Все остальные - 30 дней
    
    def get_subscription_classes_count(self, subscription_type: SubscriptionType) -> int:
        """
        Получить количество занятий по типу абонемента.
        
        Args:
            subscription_type: Тип абонемента
            
        Returns:
            Количество занятий
        """
        classes = {
            SubscriptionType.TRIAL: 1,
            SubscriptionType.SINGLE: 1,
            SubscriptionType.PACKAGE_4: 4,
            SubscriptionType.PACKAGE_8: 8,
            SubscriptionType.PACKAGE_12: 12,
            SubscriptionType.UNLIMITED: 999,  # Безлимитный
        }
        return classes[subscription_type]
    
    def get_subscription_info(self, subscription_type: SubscriptionType) -> dict:
        """
        Получить полную информацию об абонементе по типу.
        
        Args:
            subscription_type: Тип абонемента
            
        Returns:
            Словарь с информацией об абонементе
        """
        return {
            "type": subscription_type.value,
            "price": self.get_subscription_price(subscription_type),
            "classes": self.get_subscription_classes_count(subscription_type),
            "duration_days": self._get_subscription_duration_days(subscription_type),
            "description": self._get_subscription_description(subscription_type)
        }
    
    def _get_subscription_duration_days(self, subscription_type: SubscriptionType) -> int:
        """Получить продолжительность абонемента в днях."""
        if subscription_type == SubscriptionType.TRIAL:
            return 14
        elif subscription_type == SubscriptionType.SINGLE:
            return 1
        else:
            return 30
    
    def _get_subscription_description(self, subscription_type: SubscriptionType) -> str:
        """Получить описание абонемента."""
        descriptions = {
            SubscriptionType.TRIAL: "Пробный абонемент - 1 занятие на 14 дней",
            SubscriptionType.SINGLE: "Разовое занятие",
            SubscriptionType.PACKAGE_4: "Абонемент на 4 занятия (30 дней)",
            SubscriptionType.PACKAGE_8: "Абонемент на 8 занятий (30 дней)",
            SubscriptionType.PACKAGE_12: "Абонемент на 12 занятий (30 дней)",
            SubscriptionType.UNLIMITED: "Безлимитный абонемент (30 дней)",
        }
        return descriptions[subscription_type]

    # ------------------------------------------------------------------
    #  Отмена абонемента
    # ------------------------------------------------------------------

    async def cancel_subscription(self, subscription_id: str, reason: Optional[str] = None) -> Subscription:
        """Отменить (аннулировать) абонемент, выставив статус CANCELLED.

        Args:
            subscription_id: ID абонемента
            reason: Необязательная причина отмены (только логируется)
        """
        subscription = await self.get_subscription(subscription_id)

        if subscription.status == SubscriptionStatus.CANCELLED:
            logger.warning(f"Абонемент {subscription_id} уже отменён")
            return subscription

        update_data = SubscriptionUpdateData(
            status=SubscriptionStatus.CANCELLED,
            end_date=date.today(),
        )

        updated_subscription = await self._repository.update_subscription(subscription_id, update_data)

        if not updated_subscription:
            raise BusinessLogicError(f"Не удалось отменить абонемент {subscription_id}")

        log_msg = f"Абонемент {subscription_id} отменён"
        if reason:
            log_msg += f". Причина: {reason}"
        logger.info(log_msg)

        return updated_subscription

    # ------------------------------------------------------------------
    # Заморозка (freeze)
    # ------------------------------------------------------------------

    async def freeze_subscription(self, subscription_id: str, days: int, reason: str | None = None) -> Subscription:
        """Заморозить абонемент, продлив дату окончания на *days*.

        Логика:
        • Проверяем, что абонемент активен или ожидает оплаты.
        • Переводим статус в SUSPENDED.
        • Дату окончания смещаем на указанное количество дней (с учётом уже
          возможных прошлых заморозок).
        • Причина пока только логируется; отдельного поля в модели нет.
        """

        if days <= 0:
            raise BusinessLogicError("Количество дней заморозки должно быть > 0")

        subscription = await self.get_subscription(subscription_id)

        if subscription.status == SubscriptionStatus.SUSPENDED:
            # Уже заморожен – просто продлеваем срок ещё на *days*
            logger.info(
                "Абонемент %s уже заморожен, продлеваем дату окончания на %s дн.",
                subscription_id,
                days,
            )
        elif subscription.status not in (SubscriptionStatus.ACTIVE, SubscriptionStatus.PENDING):
            raise BusinessLogicError(
                f"Нельзя заморозить абонемент со статусом {subscription.status.value}"
            )

        new_end_date = subscription.end_date + timedelta(days=days)

        update_data = SubscriptionUpdateData(
            status=SubscriptionStatus.SUSPENDED,
            end_date=new_end_date,
        )

        updated_subscription = await self._repository.update_subscription(subscription_id, update_data)

        if not updated_subscription:
            raise BusinessLogicError(f"Не удалось заморозить абонемент {subscription_id}")

        logger.info(
            "Абонемент %s заморожен на %s дн. Новая дата окончания %s. Причина: %s",
            subscription_id,
            days,
            new_end_date,
            reason or "не указана",
        )

        return updated_subscription

    async def update_subscription(self, subscription_id: str, data: SubscriptionUpdateData) -> Subscription:
        """Частичное обновление абонемента через репозиторий."""
        # Если указана смена типа – пересчитаем лимиты/цену
        if data.type is not None:
            current_sub = await self.get_subscription(subscription_id)
            new_total = self.get_subscription_classes_count(data.type)
            data.total_classes = new_total
            # Обеспечим корректность used_classes
            if current_sub.used_classes > new_total:
                data.used_classes = new_total

        updated_subscription = await self._repository.update_subscription(subscription_id, data)  # type: ignore[arg-type]
        if not updated_subscription:
            raise BusinessLogicError(f"Абонемент {subscription_id} не найден")
        return updated_subscription

    # ------------------------------------------------------------------
    #  Подарить занятие (gift-class)
    # ------------------------------------------------------------------

    async def gift_class(self, subscription_id: str) -> Subscription:
        """Добавить клиенту одно бесплатное занятие.

        Логика:
        • Для обычных типов абонементов уменьшаем used_classes на 1,
          тем самым увеличивая remaining_classes.
        • Если used_classes уже 0, увеличиваем total_classes на 1.
        • Для безлимитного абонемента операция не имеет смысла.
        """
        subscription = await self.get_subscription(subscription_id)

        if subscription.type == SubscriptionType.UNLIMITED:
            raise BusinessLogicError("Безлимитному абонементу не требуется дарить занятия")

        if subscription.used_classes > 0:
            # Возвращаем одно использованное занятие
            new_used = subscription.used_classes - 1
            update_data = SubscriptionUpdateData(used_classes=new_used)
        else:
            # Если занятий ещё не использовано – расширяем лимит, увеличив total_classes
            # (через пересчёт remaining_classes)
            update_data = SubscriptionUpdateData(
                remaining_classes=subscription.remaining_classes + 1,
                total_classes=subscription.total_classes + 1,
            )

        # Если абонемент был исчерпан, делаем его активным
        if subscription.status == SubscriptionStatus.EXHAUSTED:
            update_data.status = SubscriptionStatus.ACTIVE

        updated_subscription = await self._repository.update_subscription(subscription_id, update_data)
        if not updated_subscription:
            raise BusinessLogicError(f"Не удалось обновить абонемент {subscription_id}")

        logger.info("Подарено занятие для абонемента %s. Осталось %s", updated_subscription.id, updated_subscription.remaining_classes)
        return updated_subscription 