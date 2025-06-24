from __future__ import annotations

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..models import (
    BookingCreateRequest,
    BookingResponse,
    BookingUpdateRequest,
)
from ...services.protocols.booking_service import BookingServiceProtocol
from .clients import _build_client_service
from .subscriptions import _build_subscription_service
from ...repositories.in_memory_booking_repository import InMemoryBookingRepository
from ...services.booking_service import BookingService
from ...config.settings import settings
from ...utils.exceptions import BusinessLogicError

router = APIRouter(prefix="/bookings", tags=["bookings"])


async def _build_booking_service() -> BookingServiceProtocol:  # noqa: D401
    # В production используем Google Sheets, иначе In-Memory
    if settings.environment in ("production", "development"):
        from ...repositories.google_sheets_booking_repository import GoogleSheetsBookingRepository
        from ...integrations.google_sheets import GoogleSheetsClient
        booking_repo = GoogleSheetsBookingRepository(GoogleSheetsClient())
    else:
        booking_repo = InMemoryBookingRepository()
    client_service = _build_client_service()
    subscription_service = _build_subscription_service()
    return BookingService(booking_repo, client_service, subscription_service)


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: BookingCreateRequest,
    booking_service: BookingServiceProtocol = Depends(_build_booking_service),
):
    try:
        booking = await booking_service.create_booking(request.to_model())
        return BookingResponse.model_validate(booking)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except BusinessLogicError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    booking_service: BookingServiceProtocol = Depends(_build_booking_service),
):
    booking = await booking_service.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    return BookingResponse.model_validate(booking)


@router.patch("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: str,
    request: BookingUpdateRequest,
    booking_service: BookingServiceProtocol = Depends(_build_booking_service),
):
    try:
        updated = await booking_service.update_booking(booking_id, request.to_update_data())
        return BookingResponse.model_validate(updated)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: str,
    booking_service: BookingServiceProtocol = Depends(_build_booking_service),
):
    deleted = await booking_service.cancel_booking(booking_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    return


@router.get("/", response_model=List[BookingResponse])
async def list_bookings(
    date_filter: date | None = Query(None, description="Фильтр по дате"),
    client_id: str | None = Query(None, description="Фильтр по клиенту"),
    booking_service: BookingServiceProtocol = Depends(_build_booking_service),
):
    if date_filter:
        bookings = await booking_service.get_bookings_for_date(date_filter)
    else:
        bookings = await booking_service.list_bookings()

    if client_id:
        bookings = [b for b in bookings if b.client_id == client_id]

    return [BookingResponse.model_validate(b) for b in bookings] 