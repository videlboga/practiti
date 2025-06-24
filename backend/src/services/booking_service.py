from __future__ import annotations

from datetime import date
from typing import List
import logging

from .protocols.booking_service import BookingServiceProtocol
from ..models.booking import Booking, BookingCreateData, BookingUpdateData, BookingStatus
from ..repositories.protocols.booking_repository import BookingRepositoryProtocol
from .protocols.client_service import ClientServiceProtocol
from .protocols.subscription_service import SubscriptionServiceProtocol
from .protocols.scheduler_service import SchedulerServiceProtocol


logger = logging.getLogger(__name__)


class BookingService(BookingServiceProtocol):
    """Сервис для управления записями на занятия."""

    def __init__(
        self,
        repository: BookingRepositoryProtocol,
        client_service: ClientServiceProtocol,
        subscription_service: SubscriptionServiceProtocol,
        scheduler_service: SchedulerServiceProtocol | None = None,
    ) -> None:  # noqa: D401
        self._repo = repository
        self._client_service = client_service
        self._subscription_service = subscription_service
        self._scheduler_service = scheduler_service

    async def create_booking(self, data: BookingCreateData) -> Booking:  # noqa: D401
        # Проверяем существование клиента
        client = await self._client_service.get_client(data.client_id)
        if client is None:
            raise ValueError("Клиент не найден")

        # Определяем, какой абонемент использовать
        subscription_id = data.subscription_id
        if subscription_id:
            # Явно указан – проверим принадлежность и активность
            subscription = await self._subscription_service.get_subscription(subscription_id)
            if subscription.client_id != client.id:
                raise ValueError("Абонемент принадлежит другому клиенту")
        else:
            # Ищем активный абонемент клиента
            subscription = await self._subscription_service.get_active_subscription(client.id)
            if not subscription:
                raise ValueError("У клиента нет активного абонемента для записи")
            subscription_id = subscription.id

        # Пытаемся списать занятие с абонемента (если он не безлимитный)
        try:
            await self._subscription_service.use_class(subscription_id)
        except Exception as exc:
            logger.warning(f"Не удалось списать занятие с абонемента {subscription_id}: {exc}")
            raise

        # Создаём объект бронирования и сохраняем
        booking_dict = data.model_dump()
        booking_dict["subscription_id"] = subscription_id
        booking = Booking.model_validate(booking_dict)
        await self._repo.save(booking)

        # Планируем напоминание, если доступен scheduler
        if self._scheduler_service:
            try:
                await self._scheduler_service.schedule_class_reminder(
                    client_id=client.id,
                    class_date=booking.class_date,
                    class_type=booking.class_type,
                )
            except Exception as exc:
                logger.warning(f"Не удалось запланировать напоминание для бронирования {booking.id}: {exc}")

        logger.info(f"Запись {booking.id} создана для клиента {client.name} ({client.phone})")
        return booking

    async def list_bookings(self) -> List[Booking]:  # noqa: D401
        return await self._repo.list_all()

    async def get_bookings_for_date(self, day: date) -> List[Booking]:  # noqa: D401
        return await self._repo.list_by_date(day)

    async def get_booking(self, booking_id: str) -> Booking | None:  # noqa: D401
        """Получить бронирование по ID."""
        return await self._repo.get(booking_id)

    async def update_booking(self, booking_id: str, update_data: BookingUpdateData):  # noqa: D401
        """Обновить бронирование."""
        return await self._repo.update(booking_id, update_data)

    async def cancel_booking(self, booking_id: str) -> bool:  # noqa: D401
        """Отменить бронирование с учётом бизнес-правил.

        Логика:
        1. Получаем бронирование и убеждаемся, что его можно отменить:
           • статус SCHEDULED или CONFIRMED;
           • до начала занятия > 2 часов.
        2. Возвращаем списанное занятие на абонемент (если не безлимитный).
        3. Обновляем запись: статус → CANCELLED, cancelled_at → now.
        4. Возвращаем True, если всё прошло успешно.
        """

        booking = await self._repo.get(booking_id)
        if booking is None:
            raise ValueError("Бронирование не найдено")

        # Проверяем возможность отмены
        if not booking.can_be_cancelled:
            raise ValueError("Запись нельзя отменить менее чем за 2 часа до начала")

        # Возврат занятия на абонемент (если есть и не безлимитный)
        if booking.subscription_id:
            try:
                sub = await self._subscription_service.get_subscription(booking.subscription_id)

                from ..models.subscription import SubscriptionUpdateData, SubscriptionStatus, SubscriptionType

                # Безлимитные абонементы не требуют возврата занятий
                if sub.type != SubscriptionType.UNLIMITED:
                    new_used = max(sub.used_classes - 1, 0)
                    new_remaining = (sub.remaining_classes + 1) if sub.remaining_classes is not None else None

                    update_kwargs = {"used_classes": new_used}
                    if new_remaining is not None:
                        update_kwargs["remaining_classes"] = new_remaining

                    # Если абонемент был исчерпан, вернём статус ACTIVE
                    if sub.status == SubscriptionStatus.EXHAUSTED and (new_remaining or 0) > 0:
                        update_kwargs["status"] = SubscriptionStatus.ACTIVE

                    await self._subscription_service._repository.update_subscription(  # type: ignore[attr-defined]
                        sub.id, SubscriptionUpdateData(**update_kwargs)
                    )
            except Exception as exc:
                logger.warning("Не удалось вернуть занятие на абонемент %s: %s", booking.subscription_id, exc)

        # Обновляем бронирование как отменённое
        update_data = BookingUpdateData(status=BookingStatus.CANCELLED)

        await self._repo.update(booking_id, update_data)

        logger.info("Бронирование %s отменено", booking_id)
        return True 