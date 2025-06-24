from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import date
from typing import Dict, List

from .protocols.booking_repository import BookingRepositoryProtocol
from ..models.booking import Booking, BookingUpdateData


class InMemoryBookingRepository(BookingRepositoryProtocol):
    """Хранит бронирования в памяти процесса."""

    def __init__(self) -> None:  # noqa: D401
        self._bookings: List[Booking] = []
        self._by_date: Dict[date, List[Booking]] = defaultdict(list)
        self._lock = asyncio.Lock()

    # --- базовые операции ---
    async def save(self, booking: Booking) -> None:  # noqa: D401
        async with self._lock:
            self._bookings.append(booking)
            self._by_date[booking.class_date.date()].append(booking)

    async def list_all(self) -> List[Booking]:  # noqa: D401
        async with self._lock:
            return list(self._bookings)

    async def list_by_date(self, day: date) -> List[Booking]:  # noqa: D401
        async with self._lock:
            return list(self._by_date.get(day, []))

    # --- новые операции CRUD ---
    async def get(self, booking_id: str) -> Booking | None:  # noqa: D401
        async with self._lock:
            return next((b for b in self._bookings if b.id == booking_id), None)

    async def update(self, booking_id: str, update_data: BookingUpdateData) -> Booking:  # noqa: D401
        async with self._lock:
            booking = next((b for b in self._bookings if b.id == booking_id), None)
            if booking is None:
                raise ValueError("Бронирование не найдено")
            data = update_data.model_dump(exclude_unset=True)
            for field, value in data.items():
                setattr(booking, field, value)
            # Обновляем индексацию по дате, если дата была изменена
            if 'class_date' in data:
                self._by_date = defaultdict(list)
                for b in self._bookings:
                    self._by_date[b.class_date.date()].append(b)
            return booking

    async def delete(self, booking_id: str) -> bool:  # noqa: D401
        async with self._lock:
            initial_len = len(self._bookings)
            self._bookings = [b for b in self._bookings if b.id != booking_id]
            # Перестроить индексацию по дате
            self._by_date = defaultdict(list)
            for b in self._bookings:
                self._by_date[b.class_date.date()].append(b)
            return len(self._bookings) < initial_len 