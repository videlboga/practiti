"""
📊 API роутер для аналитики

Статистика и аналитика для админ-панели йога-студии.
Принцип CyberKitty: простота превыше всего.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any
import logging
from datetime import datetime, timedelta

from ..models import (
    AnalyticsResponse, ClientStatsResponse, SubscriptionStatsResponse, 
    NotificationStatsResponse
)
from ...services.protocols.client_service import ClientServiceProtocol
from ...services.protocols.subscription_service import SubscriptionServiceProtocol
from ...services.protocols.notification_service import NotificationServiceProtocol
from ...models.client import ClientStatus
from ...models.subscription import SubscriptionStatus, SubscriptionType
from ...models.notification import NotificationStatus, NotificationType
from ...utils.exceptions import BusinessLogicError
from ...config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Упрощённый DI для совместимости с тестами ---

# Большинству REST-эндпоинтов аналитики нужны три отдельных сервиса. В юнит-тестах эти
# зависимости подменяются на асинхронные моки через `dependency_overrides`, которые
# ссылаются именно на функции `get_client_service`, `get_subscription_service`,
# `get_notification_service` (см. backend/tests/test_api.py). Поэтому для корректной
# работы тестов достаточно, чтобы эти функции существовали и возвращали реальные
# сервисы по-умолчанию. Отдельный комплексный сервис `AnalyticsService` сейчас не
# задействуется, а его импорт ломает запуск тестов. Вместо него напрямую
# инициализируем нужные сервисы ниже.

# --- Вспомогательные фабрики ---

def _build_client_service() -> ClientServiceProtocol:
    from ...repositories.in_memory_client_repository import InMemoryClientRepository
    from ...services.client_service import ClientService

    return ClientService(InMemoryClientRepository())


def _build_subscription_service() -> SubscriptionServiceProtocol:
    from ...repositories.in_memory_subscription_repository import InMemorySubscriptionRepository
    from ...services.subscription_service import SubscriptionService

    return SubscriptionService(InMemorySubscriptionRepository())


def _build_notification_service() -> NotificationServiceProtocol:
    from ...services.notification_service import NotificationService
    from ...services.telegram_sender_service import TelegramSenderService

    if settings.environment == "testing":
        from ...repositories.in_memory_notification_repository import InMemoryNotificationRepository
        notif_repo = InMemoryNotificationRepository()
    else:
        from ...repositories.google_sheets_notification_repository import GoogleSheetsNotificationRepository
        from ...integrations.google_sheets import GoogleSheetsClient
        notif_repo = GoogleSheetsNotificationRepository(GoogleSheetsClient())

    client_service = _build_client_service()
    subscription_service = _build_subscription_service()
    telegram_sender = TelegramSenderService()
    return NotificationService(notif_repo, client_service, subscription_service, telegram_sender)


# --- Реализация зависимостей, которые легко мокируются в тестах ---

def get_client_service() -> ClientServiceProtocol:  # type: ignore[override]
    return _build_client_service()


def get_subscription_service() -> SubscriptionServiceProtocol:  # type: ignore[override]
    return _build_subscription_service()


def get_notification_service() -> NotificationServiceProtocol:  # type: ignore[override]
    return _build_notification_service()


# ---------- ENDPOINTS ----------


@router.get("/overview", response_model=AnalyticsResponse)
async def get_overview_analytics(
    period: str = Query("month", description="Период: day, week, month, year"),
    client_service: ClientServiceProtocol = Depends(get_client_service),
    subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service),
    notification_service: NotificationServiceProtocol = Depends(get_notification_service)
) -> AnalyticsResponse:
    """Получить общую аналитику студии."""
    try:
        logger.info(f"Запрос общей аналитики за период: {period}")
        
        # Получаем данные из всех сервисов
        clients = await client_service.get_all_clients()
        subscriptions = await subscription_service.get_all_subscriptions()
        notifications = await notification_service.get_all_notifications()
        
        # Определяем временные рамки
        now = datetime.now()
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)  # По умолчанию месяц
        
        # Фильтруем данные по периоду
        period_clients = [c for c in clients if c.created_at >= start_date]
        period_subscriptions = [s for s in subscriptions if s.created_at >= start_date]
        period_notifications = [n for n in notifications if n.created_at >= start_date]
        
        # Формируем аналитику
        overview_data = {
            "total_clients": len(clients),
            "new_clients": len(period_clients),
            "active_clients": len([c for c in clients if c.status == ClientStatus.ACTIVE]),
            
            "total_subscriptions": len(subscriptions),
            "new_subscriptions": len(period_subscriptions),
            "active_subscriptions": len([s for s in subscriptions if s.status == SubscriptionStatus.ACTIVE]),
            
            "total_revenue": sum(s.price for s in subscriptions),
            "period_revenue": sum(s.price for s in period_subscriptions),
            
            "total_notifications": len(notifications),
            "period_notifications": len(period_notifications),
            "delivered_notifications": len([n for n in notifications if n.status == NotificationStatus.DELIVERED]),
            
            "period_start": start_date.isoformat(),
            "period_end": now.isoformat()
        }
        
        return AnalyticsResponse(
            period=period,
            data=overview_data,
            generated_at=now
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения общей аналитики: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения аналитики")


@router.get("/clients", response_model=ClientStatsResponse)
async def get_client_analytics(
    client_service: ClientServiceProtocol = Depends(get_client_service)
) -> ClientStatsResponse:
    """Получить аналитику по клиентам."""
    try:
        logger.info("Запрос аналитики по клиентам")
        
        clients = await client_service.get_all_clients()
        
        # Подсчитываем статистику
        total_clients = len(clients)
        active_clients = len([c for c in clients if c.status == ClientStatus.ACTIVE])
        
        # Новые клиенты за месяц
        month_ago = datetime.now() - timedelta(days=30)
        new_clients_this_month = len([c for c in clients if c.created_at >= month_ago])
        
        # Группировка по опыту
        clients_by_experience = {}
        for client in clients:
            exp = "experienced" if client.yoga_experience else "beginner"
            clients_by_experience[exp] = clients_by_experience.get(exp, 0) + 1
        
        # Группировка по статусу
        clients_by_status = {}
        for client in clients:
            status = client.status.value
            clients_by_status[status] = clients_by_status.get(status, 0) + 1
        
        return ClientStatsResponse(
            total_clients=total_clients,
            active_clients=active_clients,
            new_clients_this_month=new_clients_this_month,
            clients_by_experience=clients_by_experience,
            clients_by_status=clients_by_status
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения аналитики клиентов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения аналитики клиентов")


@router.get("/subscriptions", response_model=SubscriptionStatsResponse)
async def get_subscription_analytics(
    subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
) -> SubscriptionStatsResponse:
    """Получить аналитику по абонементам."""
    try:
        logger.info("Запрос аналитики по абонементам")
        
        subscriptions = await subscription_service.get_all_subscriptions()
        
        # Подсчитываем статистику
        total_subscriptions = len(subscriptions)
        active_subscriptions = len([s for s in subscriptions if s.status == SubscriptionStatus.ACTIVE])
        
        # Доходы за месяц
        month_ago = datetime.now() - timedelta(days=30)
        revenue_this_month = sum(
            s.price for s in subscriptions 
            if s.created_at >= month_ago
        )
        
        # Группировка по типу
        subscriptions_by_type = {}
        for subscription in subscriptions:
            sub_type = subscription.type.value
            subscriptions_by_type[sub_type] = subscriptions_by_type.get(sub_type, 0) + 1
        
        # Средняя стоимость абонемента
        average_subscription_value = (
            sum(s.price for s in subscriptions) / total_subscriptions
            if total_subscriptions > 0 else 0
        )
        
        return SubscriptionStatsResponse(
            total_subscriptions=total_subscriptions,
            active_subscriptions=active_subscriptions,
            revenue_this_month=revenue_this_month,
            subscriptions_by_type=subscriptions_by_type,
            average_subscription_value=average_subscription_value
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения аналитики абонементов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения аналитики абонементов")


@router.get("/notifications", response_model=NotificationStatsResponse)
async def get_notification_analytics(
    notification_service: NotificationServiceProtocol = Depends(get_notification_service)
) -> NotificationStatsResponse:
    """Получить аналитику по уведомлениям."""
    try:
        logger.info("Запрос аналитики по уведомлениям")
        
        notifications = await notification_service.get_all_notifications()
        
        # Подсчитываем статистику
        total_notifications = len(notifications)
        sent_notifications = len([n for n in notifications if n.status == NotificationStatus.SENT])
        delivered_notifications = len([n for n in notifications if n.status == NotificationStatus.DELIVERED])
        failed_notifications = len([n for n in notifications if n.status == NotificationStatus.FAILED])
        
        # Процент доставки
        delivery_rate = (
            (delivered_notifications / sent_notifications * 100)
            if sent_notifications > 0 else 0
        )
        
        # Группировка по типу
        notifications_by_type = {}
        for notification in notifications:
            notif_type = notification.notification_type.value
            notifications_by_type[notif_type] = notifications_by_type.get(notif_type, 0) + 1
        
        return NotificationStatsResponse(
            total_notifications=total_notifications,
            sent_notifications=sent_notifications,
            delivered_notifications=delivered_notifications,
            failed_notifications=failed_notifications,
            delivery_rate=delivery_rate,
            notifications_by_type=notifications_by_type
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения аналитики уведомлений: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения аналитики уведомлений")


@router.get("/revenue", response_model=AnalyticsResponse)
async def get_revenue_analytics(
    period: str = Query("month", description="Период: day, week, month, year"),
    subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
) -> AnalyticsResponse:
    """Получить аналитику доходов."""
    try:
        logger.info(f"Запрос аналитики доходов за период: {period}")
        
        subscriptions = await subscription_service.get_all_subscriptions()
        
        # Определяем временные рамки
        now = datetime.now()
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)
        
        # Фильтруем по периоду
        period_subscriptions = [s for s in subscriptions if s.created_at >= start_date]
        
        # Группируем доходы по дням
        daily_revenue = {}
        for subscription in period_subscriptions:
            date_key = subscription.created_at.date().isoformat()
            daily_revenue[date_key] = daily_revenue.get(date_key, 0) + subscription.price
        
        # Группируем по типам абонементов
        revenue_by_type = {}
        for subscription in period_subscriptions:
            sub_type = subscription.type.value
            revenue_by_type[sub_type] = revenue_by_type.get(sub_type, 0) + subscription.price
        
        revenue_data = {
            "total_revenue": sum(s.price for s in subscriptions),
            "period_revenue": sum(s.price for s in period_subscriptions),
            "daily_revenue": daily_revenue,
            "revenue_by_type": revenue_by_type,
            "average_daily_revenue": (
                sum(daily_revenue.values()) / len(daily_revenue)
                if daily_revenue else 0
            ),
            "period_start": start_date.isoformat(),
            "period_end": now.isoformat()
        }
        
        return AnalyticsResponse(
            period=period,
            data=revenue_data,
            generated_at=now
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения аналитики доходов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения аналитики доходов")


# --------------------------------------------------------------
#  Alias for dashboard (frontend expects /dashboard/metrics)
# --------------------------------------------------------------


@router.get("/dashboard/metrics", response_model=AnalyticsResponse)
async def get_dashboard_metrics(  # noqa: D401
    period: str = Query("month", description="Период: day, week, month, year"),
    client_service: ClientServiceProtocol = Depends(get_client_service),
    subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service),
    notification_service: NotificationServiceProtocol = Depends(get_notification_service),
) -> AnalyticsResponse:
    """Alias для фронтенда: /dashboard/metrics → overview."""
    return await get_overview_analytics(period, client_service, subscription_service, notification_service)
