"""
💳 Google Sheets репозиторий абонементов CyberKitty Practiti

Реализация SubscriptionRepositoryProtocol для хранения данных в Google Sheets.
"""

from datetime import datetime, timedelta, date
from typing import List, Optional
import uuid

from ..integrations.google_sheets import GoogleSheetsClient
from ..models.subscription import (
    Subscription,
    SubscriptionCreateData,
    SubscriptionStatus,
    SubscriptionType,
    SubscriptionUpdateData,
)
from ..utils.logger import get_logger, log_subscription_action
from ..utils.exceptions import GoogleSheetsError, SubscriptionNotFoundError
from .protocols.subscription_repository import SubscriptionRepositoryProtocol

logger = get_logger(__name__)

# Константа с параметрами абонементов (кол-во занятий, длительность, цена)
SUBSCRIPTION_TYPES = {
    SubscriptionType.TRIAL:    {"classes": 1,  "duration_days": 14, "price": 500},
    SubscriptionType.SINGLE:   {"classes": 1,  "duration_days": 30, "price": 1100},
    SubscriptionType.PACKAGE_4:  {"classes": 4,  "duration_days": 30, "price": 3200},
    SubscriptionType.PACKAGE_8:  {"classes": 8,  "duration_days": 30, "price": 7000},
    SubscriptionType.PACKAGE_12: {"classes": 12, "duration_days": 30, "price": 9000},
    SubscriptionType.UNLIMITED: {"classes": 9999, "duration_days": 30, "price": 10800},
}

class GoogleSheetsSubscriptionRepository(SubscriptionRepositoryProtocol):
    """
    Репозиторий абонементов для Google Sheets.
    
    Структура листа "Subscriptions":
    A: ID | B: Client_ID | C: Type | D: Status | E: Start_Date | 
    F: End_Date | G: Classes_Total | H: Classes_Remaining | I: Created_At
    """
    
    SHEET_NAME = "Subscriptions"
    HEADER_ROW = [
        "ID", "Client_ID", "Type", "Status", "Start_Date", 
        "End_Date", "Classes_Total", "Classes_Remaining", "Created_At"
    ]
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets_client = sheets_client
        logger.info("Initialized Google Sheets Subscription Repository")
    
    async def _ensure_headers(self) -> None:
        # Убеждаемся, что лист существует
        await self.sheets_client.ensure_sheet_exists(self.SHEET_NAME)

        try:
            first_row = await self.sheets_client.read_range("A1:I1", self.SHEET_NAME)
            if not first_row or first_row[0] != self.HEADER_ROW:
                await self.sheets_client.write_range("A1:I1", [self.HEADER_ROW], self.SHEET_NAME)
                logger.info("Headers set for Subscriptions sheet")
        except GoogleSheetsError:
            await self.sheets_client.write_range("A1:I1", [self.HEADER_ROW], self.SHEET_NAME)
            logger.info("Created Subscriptions sheet with headers")
    
    def _to_row(self, sub: Subscription) -> List[str]:
        return [
            sub.id,
            sub.client_id,
            sub.type.value,
            sub.status.value,
            sub.start_date.isoformat() if sub.start_date else "",
            sub.end_date.isoformat() if sub.end_date else "",
            str(sub.total_classes),
            str(sub.remaining_classes),
            sub.created_at.isoformat()
        ]
    
    def _from_row(self, row: List[str]) -> Optional[Subscription]:
        try:
            if len(row) < 9:
                return None
            
            details = SUBSCRIPTION_TYPES.get(SubscriptionType(row[2]))
            
            return Subscription(
                id=row[0],
                client_id=row[1],
                type=SubscriptionType(row[2]),
                status=SubscriptionStatus(row[3]),
                start_date=datetime.fromisoformat(row[4]).date() if row[4] else None,
                end_date=datetime.fromisoformat(row[5]).date() if row[5] else None,
                total_classes=int(row[6]),
                used_classes=int(details["classes"]) - int(row[7]) if details else 0,
                price=details["price"] if details else 0,
                created_at=datetime.fromisoformat(row[8]),
            )
        except (ValueError, IndexError, KeyError) as e:
            logger.error(f"Error parsing subscription row: {e}", row=row)
            return None

    async def _find_row_num(self, subscription_id: str) -> Optional[int]:
        try:
            ids_data = await self.sheets_client.read_range("A:A", self.SHEET_NAME)
            for i, row_data in enumerate(ids_data, 1):
                if row_data and row_data[0] == subscription_id:
                    return i
            return None
        except GoogleSheetsError:
            return None

    async def save_subscription(self, data: SubscriptionCreateData) -> Subscription:
        await self._ensure_headers()
        
        details = SUBSCRIPTION_TYPES[data.type]
        start_date = data.start_date or datetime.utcnow()
        end_date = start_date + timedelta(days=details["duration_days"])

        subscription = Subscription(
            id=str(uuid.uuid4()),
            client_id=data.client_id,
            type=data.type,
            status=SubscriptionStatus.ACTIVE,
            start_date=start_date if isinstance(start_date, date) else start_date.date(),
            end_date=end_date if isinstance(end_date, date) else end_date.date(),
            total_classes=details["classes"],
            used_classes=0,
            price=details["price"],
            created_at=datetime.utcnow(),
        )
        
        try:
            row_data = self._to_row(subscription)
            await self.sheets_client.append_rows([row_data], self.SHEET_NAME)
            # Логируем действие с абонементом (id первым аргументом)
            log_subscription_action(subscription.id, "created", f"client={subscription.client_id}")
            return subscription
        except GoogleSheetsError as e:
            logger.error(f"Failed to save subscription: {e}")
            raise

    async def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        row_num = await self._find_row_num(subscription_id)
        if not row_num:
            return None
        
        try:
            data = await self.sheets_client.read_range(f"A{row_num}:I{row_num}", self.SHEET_NAME)
            if not data or not data[0]:
                return None
            return self._from_row(data[0])
        except GoogleSheetsError as e:
            logger.error(f"Failed to get subscription by ID {subscription_id}: {e}")
            return None

    # ------------------------------------------------------------------
    #  Обновление абонемента (контракт репозитория)
    # ------------------------------------------------------------------

    async def update_subscription(self, subscription_id: str, update_data):  # type: ignore[override]
        """Обновить абонемент частично.

        Args:
            subscription_id: ID абонемента
            update_data: SubscriptionUpdateData или Subscription
        """

        # Lazy import, чтобы избежать циклических зависимостей
        from ..models.subscription import SubscriptionUpdateData, Subscription

        # Если пришёл уже готовый объект Subscription – просто сохраняем
        if isinstance(update_data, Subscription):
            subscription = update_data
        else:
            if not isinstance(update_data, SubscriptionUpdateData):
                raise ValueError("update_data must be Subscription or SubscriptionUpdateData")

            subscription = await self.get_subscription_by_id(subscription_id)
            if not subscription:
                raise SubscriptionNotFoundError(subscription_id)

            # Применяем патч
            if update_data.status is not None:
                subscription.status = update_data.status
            if update_data.used_classes is not None:
                subscription.used_classes = update_data.used_classes
            if update_data.payment_confirmed is not None:
                subscription.payment_confirmed = update_data.payment_confirmed
                if update_data.payment_confirmed:
                    subscription.payment_confirmed_at = datetime.utcnow()
            if update_data.end_date is not None:
                subscription.end_date = update_data.end_date
            if update_data.remaining_classes is not None:
                # Обновляем оставшиеся занятия через пересчёт used_classes
                subscription.used_classes = subscription.total_classes - update_data.remaining_classes

        # Сохраняем изменённый объект целиком
        row_num = await self._find_row_num(subscription.id)
        if not row_num:
            raise SubscriptionNotFoundError(f"Subscription {subscription.id} not found for update.")

        try:
            row_data = self._to_row(subscription)
            await self.sheets_client.write_range(f"A{row_num}:I{row_num}", [row_data], self.SHEET_NAME)
            log_subscription_action(subscription.id, "updated", f"client={subscription.client_id}")
            return subscription
        except GoogleSheetsError as e:
            logger.error(f"Failed to update subscription {subscription.id}: {e}")
            raise

    async def list_subscriptions(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Subscription]:
        """Получить список абонементов с опциональной пагинацией."""
        try:
            all_data = await self.sheets_client.read_range("A2:I", self.SHEET_NAME)
            subscriptions: List[Subscription] = []
            for row in all_data:
                if row and row[0]:
                    sub = self._from_row(row)
                    if sub:
                        subscriptions.append(sub)

            # Пагинация на уровне Python (Google API не поддерживает offset)
            if offset is not None:
                subscriptions = subscriptions[offset:]
            if limit is not None:
                subscriptions = subscriptions[:limit]

            return subscriptions
        except GoogleSheetsError as e:
            logger.error(f"Failed to list subscriptions: {e}")
            return []
            
    async def get_subscriptions_by_client_id(self, client_id: str) -> List[Subscription]:
        all_subs = await self.list_subscriptions()
        return [sub for sub in all_subs if sub.client_id == client_id]

    async def get_subscriptions_by_status(self, status: SubscriptionStatus) -> List[Subscription]:
        all_subs = await self.list_subscriptions()
        return [sub for sub in all_subs if sub.status == status]

    # ---------------------------------------------------------------------
    # Необходимые методы протокола, пока не требуются в бизнес-логике.
    # Реализуем простыми/наивными вариантами, чтобы снять абстрактность.
    # ---------------------------------------------------------------------

    async def delete_subscription(self, subscription_id: str) -> bool:  # noqa: D401
        """Удаление из Google Sheets сейчас не поддерживается."""
        logger.warning("Delete subscription not implemented for Google Sheets backend")
        return False

    async def get_active_subscriptions_by_client_id(self, client_id: str) -> List[Subscription]:  # noqa: D401
        subs = await self.get_subscriptions_by_client_id(client_id)
        return [s for s in subs if s.status == SubscriptionStatus.ACTIVE and s.is_active]

    async def get_expiring_subscriptions(self, days_before: int = 3) -> List[Subscription]:  # noqa: D401
        subs = await self.list_subscriptions()
        upcoming = []
        today = datetime.utcnow().date()
        for s in subs:
            if s.end_date and 0 <= (s.end_date - today).days <= days_before:
                upcoming.append(s)
        return upcoming

    async def count_subscriptions(self) -> int:
        subs = await self.list_subscriptions()
        return len(subs)

    async def count_subscriptions_by_client(self, client_id: str) -> int:
        subs = await self.get_subscriptions_by_client_id(client_id)
        return len(subs) 