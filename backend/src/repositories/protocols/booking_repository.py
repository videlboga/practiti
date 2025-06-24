from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List

from ...models.booking import Booking, BookingUpdateData


class BookingRepositoryProtocol(ABC):
    """Абстрактный репозиторий бронирований."""

    @abstractmethod
    async def save(self, booking: Booking) -> None:  # noqa: D401
        """Сохранить бронирование."""

    @abstractmethod
    async def list_all(self) -> List[Booking]:  # noqa: D401
        """Получить все бронирования."""

    @abstractmethod
    async def list_by_date(self, day: date) -> List[Booking]:  # noqa: D401
        """Получить бронирования на дату."""

    # --- новые методы CRUD ---

    @abstractmethod
    async def get(self, booking_id: str) -> Booking | None:  # noqa: D401
        """Получить бронирование по ID."""

    @abstractmethod
    async def update(self, booking_id: str, update_data: BookingUpdateData) -> Booking:  # noqa: D401
        """Обновить бронирование и вернуть обновлённый объект."""

    @abstractmethod
    async def delete(self, booking_id: str) -> bool:  # noqa: D401
        """Удалить бронирование по ID. Возвращает True, если удалено."""