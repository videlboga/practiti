"""
💳 API роутер для управления абонементами

CRUD операции для абонементов йога-студии.
Принцип CyberKitty: простота превыше всего.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging
import math
import sys
from datetime import date

from ..models import (
    SubscriptionCreateRequest, SubscriptionResponse, UseClassRequest,
    APIResponse, PaginationParams, PaginatedResponse
)
from ...services.protocols.subscription_service import SubscriptionServiceProtocol
from ...models.subscription import SubscriptionStatus, SubscriptionType
from ...utils.exceptions import BusinessLogicError, ValidationError
from ...config.settings import settings
from ...services.subscription_service import SubscriptionService
from ...repositories.in_memory_subscription_repository import InMemorySubscriptionRepository

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------- Фабрики для DI ----------


def _create_subscription_repository():
    """Фабрика репозитория абонементов в зависимости от окружения."""

    global _subscription_repo  # type: ignore[attr-defined]

    try:
        return _subscription_repo  # type: ignore[misc]
    except NameError:
        pass  # создаём ниже

    # Во время тестов используем In-Memory, во всех остальных – Google Sheets
    if "pytest" in sys.modules:
        from ...repositories.in_memory_subscription_repository import InMemorySubscriptionRepository
        _subscription_repo = InMemorySubscriptionRepository()  # type: ignore
    else:
        from ...repositories.google_sheets_subscription_repository import GoogleSheetsSubscriptionRepository
        from ...integrations.google_sheets import GoogleSheetsClient
        _subscription_repo = GoogleSheetsSubscriptionRepository(GoogleSheetsClient())  # type: ignore

    return _subscription_repo  # type: ignore


def _build_subscription_service() -> SubscriptionServiceProtocol:
    """Создать экземпляр SubscriptionService."""
    return SubscriptionService(_create_subscription_repository())


# Dependency injection для сервисов
async def get_subscription_service() -> SubscriptionServiceProtocol:
    """Получение сервиса абонементов."""
    return _build_subscription_service()


@router.get("/", response_model=PaginatedResponse)
async def get_subscriptions(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(20, ge=1, le=100, description="Количество на странице"),
    status: Optional[SubscriptionStatus] = Query(None, description="Фильтр по статусу"),
    subscription_type: Optional[SubscriptionType] = Query(None, description="Фильтр по типу"),
    client_id: Optional[str] = Query(None, description="Фильтр по клиенту"),
    subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
) -> PaginatedResponse:
    """Получить список абонементов с пагинацией."""
    try:
        logger.info(f"Запрос списка абонементов: page={page}, limit={limit}, status={status}")
        
        # Получаем абонементы с фильтрами
        if client_id:
            subscriptions = await subscription_service.get_client_subscriptions(client_id)
        elif status:
            subscriptions = await subscription_service.get_subscriptions_by_status(status)
        else:
            subscriptions = await subscription_service.get_all_subscriptions()
        
        # Дополнительная фильтрация по типу
        if subscription_type:
            subscriptions = [s for s in subscriptions if s.type == subscription_type]
        
        # Пагинация
        total = len(subscriptions)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_subscriptions = subscriptions[start_idx:end_idx]
        
        # Конвертируем в response модели
        subscription_responses = [
            SubscriptionResponse.from_orm(subscription) for subscription in paginated_subscriptions
        ]
        
        return PaginatedResponse(
            items=subscription_responses,
            total=total,
            page=page,
            limit=limit,
            pages=math.ceil(total / limit) if total > 0 else 1
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения списка абонементов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка абонементов")


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
) -> SubscriptionResponse:
    """Получить абонемент по ID."""
    try:
        logger.info(f"Запрос абонемента: {subscription_id}")
        
        subscription = await subscription_service.get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Абонемент не найден")
        
        return SubscriptionResponse.from_orm(subscription)
        
    except BusinessLogicError as e:
        logger.warning(f"Абонемент не найден: {subscription_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка получения абонемента {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения абонемента")


@router.post("/", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    request: SubscriptionCreateRequest,
    subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
) -> SubscriptionResponse:
    """Создать новый абонемент."""
    try:
        logger.info(f"Создание абонемента: клиент={request.client_id}, тип={request.subscription_type}")
        
        # Конвертируем request в модель создания
        from ...models.subscription import SubscriptionCreateData
        
        create_data = SubscriptionCreateData(
            client_id=request.client_id,
            type=request.subscription_type,
            # start_date не передаём, будет default_factory=date.today()
        )
        
        subscription = await subscription_service.create_subscription(create_data)
        
        logger.info(f"Абонемент создан: {subscription.id}")
        return SubscriptionResponse.from_orm(subscription)
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка бизнес-логики при создании абонемента: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Ошибка валидации при создании абонемента: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка создания абонемента: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания абонемента")


@router.post("/{subscription_id}/use-class", response_model=SubscriptionResponse)
async def use_class(
    subscription_id: str,
    request: UseClassRequest,
    subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
) -> SubscriptionResponse:
    """Использовать занятие из абонемента."""
    try:
        logger.info(f"Использование занятия: абонемент={subscription_id}, дата={request.class_date}")
        
        # Проверяем, что subscription_id в URL совпадает с request
        if request.subscription_id != subscription_id:
            raise HTTPException(
                status_code=400, 
                detail="ID абонемента в URL не совпадает с данными запроса"
            )
        
        subscription = await subscription_service.use_class(subscription_id)
        
        logger.info(f"Занятие использовано: {subscription_id}")
        return SubscriptionResponse.from_orm(subscription)
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка при использовании занятия: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка использования занятия {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка использования занятия")


@router.patch("/{subscription_id}/freeze", response_model=SubscriptionResponse)
async def freeze_subscription(
    subscription_id: str,
    days: int = Query(..., ge=1, le=90, description="Количество дней заморозки"),
    reason: Optional[str] = Query(None, max_length=500, description="Причина заморозки"),
    subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
) -> SubscriptionResponse:
    """Заморозить абонемент."""
    try:
        logger.info(f"Заморозка абонемента: {subscription_id} на {days} дней")
        
        subscription = await subscription_service.freeze_subscription(
            subscription_id=subscription_id,
            days=days,
            reason=reason
        )
        
        logger.info(f"Абонемент заморожен: {subscription_id}")
        return SubscriptionResponse.from_orm(subscription)
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка при заморозке абонемента: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка заморозки абонемента {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка заморозки абонемента")


@router.delete("/{subscription_id}", response_model=APIResponse)
async def cancel_subscription(
    subscription_id: str,
    reason: Optional[str] = Query(None, max_length=500, description="Причина отмены"),
    subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
) -> APIResponse:
    """Отменить абонемент."""
    try:
        logger.info(f"Отмена абонемента: {subscription_id}")
        
        await subscription_service.cancel_subscription(subscription_id, reason)
        
        logger.info(f"Абонемент отменен: {subscription_id}")
        return APIResponse(
            success=True,
            message=f"Абонемент {subscription_id} успешно отменен"
        )
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка при отмене абонемента: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка отмены абонемента {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отмены абонемента")


# ---------------------------------------------------------------------------
#  Подтверждение оплаты
# ---------------------------------------------------------------------------


@router.patch("/{subscription_id}/confirm-payment", response_model=SubscriptionResponse)
async def confirm_subscription_payment(
    subscription_id: str,
    subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
) -> SubscriptionResponse:
    """Подтвердить оплату и активировать абонемент."""
    try:
        logger.info(f"Подтверждение оплаты абонемента: {subscription_id}")

        subscription = await subscription_service.confirm_payment(subscription_id)

        return SubscriptionResponse.from_orm(subscription)

    except BusinessLogicError as e:
        logger.warning(f"Бизнес-ошибка подтверждения оплаты: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка подтверждения оплаты {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка подтверждения оплаты")
