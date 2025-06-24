from __future__ import annotations

"""
📅 Google Sheets репозиторий бронирований Practiti

Реализация BookingRepositoryProtocol, хранит данные в листе "Bookings" Google Sheets.
Структура листа:
A: ID | B: Client_ID | C: Class_Date | D: Class_Type | E: Status | F: Created_At |
G: Subscription_ID | H: Teacher | I: Duration | J: Notes
"""

from datetime import datetime, date
from typing import List, Optional
import uuid

from .protocols.booking_repository import BookingRepositoryProtocol
from ..integrations.google_sheets import GoogleSheetsClient
from ..models.booking import Booking, BookingStatus, BookingUpdateData
from ..utils.exceptions import GoogleSheetsError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class GoogleSheetsBookingRepository(BookingRepositoryProtocol):
    SHEET_NAME = "Bookings"
    HEADER_ROW = [
        "ID",
        "Client_ID",
        "Class_Date",
        "Class_Type",
        "Status",
        "Created_At",
        "Subscription_ID",
        "Teacher",
        "Duration",
        "Notes",
    ]

    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets_client = sheets_client
        logger.info("Initialized Google Sheets Booking Repository")

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------
    async def _ensure_headers(self) -> None:
        # Убеждаемся, что лист существует
        await self.sheets_client.ensure_sheet_exists(self.SHEET_NAME)

        try:
            first_row = await self.sheets_client.read_range("A1:J1", self.SHEET_NAME)
        except GoogleSheetsError:
            # Ошибка чтения — продолжаем как отсутствие заголовков
            first_row = []

        if not first_row or (first_row and first_row[0] != self.HEADER_ROW):
            await self.sheets_client.write_range("A1:J1", [self.HEADER_ROW], self.SHEET_NAME)
            logger.info("Headers set for Bookings sheet")

    def _to_row(self, booking: Booking) -> List[str]:
        return [
            booking.id,
            booking.client_id,
            booking.class_date.isoformat(),
            booking.class_type,
            booking.status.value,
            booking.created_at.isoformat(),
            booking.subscription_id or "",
            booking.teacher_name or "",
            str(booking.class_duration),
            booking.notes or "",
        ]

    def _from_row(self, row: List[str]) -> Optional[Booking]:
        try:
            if len(row) < 10:
                return None
            return Booking(
                id=row[0],
                client_id=row[1],
                class_date=datetime.fromisoformat(row[2]),
                class_type=row[3],
                status=BookingStatus(row[4]),
                created_at=datetime.fromisoformat(row[5]) if row[5] else datetime.utcnow(),
                subscription_id=row[6] or None,
                teacher_name=row[7] or None,
                class_duration=int(row[8]) if row[8] else 90,
                notes=row[9] or None,
            )
        except (ValueError, IndexError) as exc:
            logger.error(f"Failed to parse booking row: {exc}")
            return None

    async def _find_row(self, booking_id: str) -> Optional[int]:
        ids = await self.sheets_client.read_range("A:A", self.SHEET_NAME)
        for idx, row in enumerate(ids, start=1):
            if row and row[0] == booking_id:
                return idx
        return None

    # ------------------------------------------------------------------
    # CRUD реализация
    # ------------------------------------------------------------------
    async def save(self, booking: Booking) -> None:  # noqa: D401
        await self._ensure_headers()
        try:
            await self.sheets_client.append_rows([self._to_row(booking)], self.SHEET_NAME)
            logger.info(f"Booking {booking.id} saved for client {booking.client_id}")
        except GoogleSheetsError as e:
            logger.error(f"Failed to save booking: {e}")
            raise

    async def list_all(self) -> List[Booking]:  # noqa: D401
        # Убеждаемся, что лист и заголовки существуют
        await self._ensure_headers()
        data = await self.sheets_client.read_range("A2:J", self.SHEET_NAME)
        bookings: List[Booking] = []
        for row in data:
            if row and row[0]:
                bk = self._from_row(row)
                if bk:
                    bookings.append(bk)
        return bookings

    async def list_by_date(self, day: date) -> List[Booking]:  # noqa: D401
        all_b = await self.list_all()
        return [b for b in all_b if b.class_date.date() == day]

    async def get(self, booking_id: str) -> Booking | None:  # noqa: D401
        row_num = await self._find_row(booking_id)
        if not row_num:
            return None
        data = await self.sheets_client.read_range(f"A{row_num}:J{row_num}", self.SHEET_NAME)
        if not data or not data[0]:
            return None
        return self._from_row(data[0])

    async def update(self, booking_id: str, update_data: BookingUpdateData) -> Booking:  # noqa: D401
        row_num = await self._find_row(booking_id)
        if not row_num:
            raise ValueError("Бронирование не найдено")

        # Читаем текущую строку
        raw_row = await self.sheets_client.read_range(f"A{row_num}:J{row_num}", self.SHEET_NAME)
        if not raw_row or not raw_row[0]:
            raise ValueError("Бронирование не найдено")
        booking = self._from_row(raw_row[0])
        if not booking:
            raise ValueError("Некорректные данные бронирования")

        data_dict = update_data.model_dump(exclude_unset=True)
        for field, value in data_dict.items():
            setattr(booking, field, value)

        # Перезаписываем строку
        await self.sheets_client.write_range(
            f"A{row_num}:J{row_num}", [self._to_row(booking)], self.SHEET_NAME)
        logger.info(f"Booking {booking.id} updated")
        return booking

    async def delete(self, booking_id: str) -> bool:  # noqa: D401
        row_num = await self._find_row(booking_id)
        if not row_num:
            return False
        try:
            await self.sheets_client.clear_range(f"A{row_num}:J{row_num}", self.SHEET_NAME)
            logger.info(f"Booking {booking_id} deleted")
            return True
        except GoogleSheetsError as e:
            logger.error(f"Failed to delete booking: {e}")
            return False 