"""
🔔 API роутер для управления уведомлениями

CRUD операции для уведомлений йога-студии.
Принцип CyberKitty: простота превыше всего.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging
import math
import sys

from ..models import (
    NotificationCreateRequest, NotificationResponse, NotificationSearchRequest,
    APIResponse, PaginationParams, PaginatedResponse
)
from ...services.protocols.notification_service import NotificationServiceProtocol
from ...models.notification import NotificationStatus, NotificationType, NotificationPriority
from ...utils.exceptions import BusinessLogicError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency injection для сервисов
async def get_notification_service() -> NotificationServiceProtocol:
    """Получение сервиса уведомлений."""
    # Временная заглушка - в реальном приложении будет DI
    from ...repositories.in_memory_notification_repository import InMemoryNotificationRepository
    from ...repositories.in_memory_client_repository import InMemoryClientRepository
    from ...repositories.in_memory_subscription_repository import InMemorySubscriptionRepository
    from ...services.notification_service import NotificationService
    from ...services.client_service import ClientService
    from ...services.subscription_service import SubscriptionService
    from ...services.telegram_sender_service import TelegramSenderService

    # Во время запуска pytest всегда берём репозиторий в памяти, чтобы исключить
    # внешние зависимости и обеспечить изоляцию тестов.
    if "pytest" in sys.modules:
        notification_repository = InMemoryNotificationRepository()
    else:
        try:
            from ...repositories.google_sheets_notification_repository import GoogleSheetsNotificationRepository
            from ...integrations.google_sheets import GoogleSheetsClient
            notification_repository = GoogleSheetsNotificationRepository(GoogleSheetsClient())
        except Exception as e:  # pragma: no cover – graceful fallback
            logger.error(
                f"Не удалось создать GoogleSheetsNotificationRepository: {e}. Переключаюсь на InMemory."
            )
            notification_repository = InMemoryNotificationRepository()
    
    # Создаем сервисы (используем такие же фабрики, как в других роутерах)
    from ...api.routers.clients import _build_client_service as _cs
    from ...api.routers.subscriptions import _build_subscription_service as _ss

    client_service = _cs()
    subscription_service = _ss()
    
    return NotificationService(notification_repository, client_service, subscription_service, TelegramSenderService())


@router.get("/", response_model=PaginatedResponse)
async def get_notifications(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(20, ge=1, le=100, description="Количество на странице"),
    status: Optional[NotificationStatus] = Query(None, description="Фильтр по статусу"),
    notification_type: Optional[NotificationType] = Query(None, description="Фильтр по типу"),
    priority: Optional[NotificationPriority] = Query(None, description="Фильтр по приоритету"),
    client_id: Optional[str] = Query(None, description="Фильтр по клиенту"),
    notification_service: NotificationServiceProtocol = Depends(get_notification_service)
) -> PaginatedResponse:
    """Получить список уведомлений с пагинацией."""
    try:
        logger.info(f"Запрос списка уведомлений: page={page}, limit={limit}, status={status}")
        
        # Получаем уведомления с фильтрами
        notifications = await notification_service.get_all_notifications()
        
        # Применяем фильтры
        if client_id:
            notifications = [n for n in notifications if n.client_id == client_id]
        if status:
            notifications = [n for n in notifications if n.status == status]
        if notification_type:
            notifications = [n for n in notifications if n.type == notification_type]
        if priority:
            notifications = [n for n in notifications if n.priority == priority]
        
        # Пагинация
        total = len(notifications)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_notifications = notifications[start_idx:end_idx]
        
        # Конвертируем в response модели
        notification_responses = [
            NotificationResponse.from_notification(notification) for notification in paginated_notifications
        ]
        
        return PaginatedResponse(
            items=notification_responses,
            total=total,
            page=page,
            limit=limit,
            pages=math.ceil(total / limit) if total > 0 else 1
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения списка уведомлений: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка уведомлений")


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    notification_service: NotificationServiceProtocol = Depends(get_notification_service)
) -> NotificationResponse:
    """Получить уведомление по ID."""
    try:
        logger.info(f"Запрос уведомления: {notification_id}")
        
        notification = await notification_service.get_notification(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Уведомление не найдено")
        
        return NotificationResponse.from_notification(notification)
        
    except BusinessLogicError as e:
        logger.warning(f"Уведомление не найдено: {notification_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка получения уведомления {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения уведомления")


@router.post("/", response_model=NotificationResponse, status_code=201)
async def create_notification(
    request: NotificationCreateRequest,
    notification_service: NotificationServiceProtocol = Depends(get_notification_service)
) -> NotificationResponse:
    """Создать новое уведомление."""
    try:
        logger.info(f"Создание уведомления: клиент={request.client_id}, тип={request.notification_type}")
        
        # Конвертируем request в модель создания
        from ...models.notification import NotificationCreateData
        
        create_data = NotificationCreateData(
            client_id=request.client_id,
            type=request.notification_type,  # Преобразуем notification_type -> type
            title=request.title,
            message=request.message,
            priority=request.priority,
            scheduled_at=request.scheduled_at,
            metadata=request.metadata
        )
        
        notification = await notification_service.create_notification(create_data)
        
        logger.info(f"Уведомление создано: {notification.id}")
        return NotificationResponse.from_notification(notification)
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка бизнес-логики при создании уведомления: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Ошибка валидации при создании уведомления: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка создания уведомления: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания уведомления")


@router.post("/{notification_id}/send", response_model=NotificationResponse)
async def send_notification(
    notification_id: str,
    notification_service: NotificationServiceProtocol = Depends(get_notification_service)
) -> NotificationResponse:
    """Отправить уведомление немедленно."""
    try:
        logger.info(f"Отправка уведомления: {notification_id}")
        
        # Отправляем уведомление (возвращает bool)
        success = await notification_service.send_notification(notification_id)
        if not success:
            raise HTTPException(status_code=400, detail="Не удалось отправить уведомление")
        
        # Получаем обновленное уведомление
        notification = await notification_service.get_notification(notification_id)
        
        logger.info(f"Уведомление отправлено: {notification_id}")
        return NotificationResponse.from_notification(notification)
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка при отправке уведомления: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отправки уведомления")


@router.delete("/{notification_id}", response_model=APIResponse)
async def delete_notification(
    notification_id: str,
    notification_service: NotificationServiceProtocol = Depends(get_notification_service)
) -> APIResponse:
    """Удалить уведомление."""
    try:
        logger.info(f"Удаление уведомления: {notification_id}")
        
        await notification_service.delete_notification(notification_id)
        
        logger.info(f"Уведомление удалено: {notification_id}")
        return APIResponse(
            success=True,
            message=f"Уведомление {notification_id} успешно удалено"
        )
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка при удалении уведомления: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка удаления уведомления {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления уведомления")
