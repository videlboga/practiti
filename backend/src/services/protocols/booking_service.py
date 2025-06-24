from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List

from ...models.booking import Booking, BookingCreateData, BookingUpdateData


class BookingServiceProtocol(ABC):
    """Абстрактный сервис бронирований."""

    # --- базовые методы ---
    @abstractmethod
    async def create_booking(self, data: BookingCreateData) -> Booking:  # noqa: D401
        """Создать запись на занятие."""

    @abstractmethod
    async def list_bookings(self) -> List[Booking]:  # noqa: D401
        """Получить все записи."""

    @abstractmethod
    async def get_bookings_for_date(self, day: date) -> List[Booking]:  # noqa: D401
        """Записи на определённый день."""

    # --- новые методы CRUD ---
    @abstractmethod
    async def get_booking(self, booking_id: str) -> Booking | None:  # noqa: D401
        """Получить запись по ID."""

    @abstractmethod
    async def update_booking(self, booking_id: str, update_data: BookingUpdateData) -> Booking:  # noqa: D401
        """Обновить запись."""

    @abstractmethod
    async def cancel_booking(self, booking_id: str) -> bool:  # noqa: D401
        """Отменить запись."""