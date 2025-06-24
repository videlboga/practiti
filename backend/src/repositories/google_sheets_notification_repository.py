"""
🔔 Google Sheets репозиторий уведомлений CyberKitty Practiti

Реализация NotificationRepositoryProtocol для хранения данных в Google Sheets.
"""

from datetime import datetime
from typing import List, Optional
import uuid

from ..integrations.google_sheets import GoogleSheetsClient
from ..models.notification import Notification, NotificationStatus, NotificationChannel, NotificationType, NotificationPriority
from ..utils.logger import get_logger
from ..utils.exceptions import GoogleSheetsError
from .protocols.notification_repository import NotificationRepositoryProtocol

logger = get_logger(__name__)


class GoogleSheetsNotificationRepository(NotificationRepositoryProtocol):
    """
    Репозиторий уведомлений для Google Sheets.
    
    Структура листа "Notifications":
    A: ID | B: Client_ID | C: Type | D: Title | E: Message | F: Status | G: Priority | H: Channel |
    I: Created_At | J: Scheduled_At | K: Sent_At | L: Delivered_At | M: Failed_At | N: Retry_Count
    """
    
    SHEET_NAME = "Notifications"
    HEADER_ROW = [
        "ID", "Client_ID", "Type", "Title", "Message", "Status", "Priority", "Channel",
        "Created_At", "Scheduled_At", "Sent_At", "Delivered_At", "Failed_At", "Retry_Count"
    ]
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets_client = sheets_client
        logger.info("Initialized Google Sheets Notification Repository")
    
    async def _ensure_headers(self) -> None:
        # Убеждаемся, что лист существует
        await self.sheets_client.ensure_sheet_exists(self.SHEET_NAME)

        try:
            first_row = await self.sheets_client.read_range("A1:N1", self.SHEET_NAME)
            if not first_row or first_row[0] != self.HEADER_ROW:
                await self.sheets_client.write_range("A1:N1", [self.HEADER_ROW], self.SHEET_NAME)
                logger.info("Headers set for Notifications sheet")
        except GoogleSheetsError:
            await self.sheets_client.write_range("A1:N1", [self.HEADER_ROW], self.SHEET_NAME)
            logger.info("Created Notifications sheet with headers")

    def _to_row(self, notif: Notification) -> List[str]:
        """Преобразовать модель уведомления в строку для Google Sheets."""
        return [
            notif.id,
            notif.client_id,
            notif.type.value,
            notif.title,
            notif.message,
            notif.status.value,
            notif.priority.value,
            notif.channel.value,
            notif.created_at.isoformat(),
            notif.scheduled_at.isoformat() if notif.scheduled_at else "",
            notif.sent_at.isoformat() if notif.sent_at else "",
            notif.delivered_at.isoformat() if notif.delivered_at else "",
            notif.failed_at.isoformat() if notif.failed_at else "",
            str(notif.retry_count)
        ]
    
    def _from_row(self, row: List[str]) -> Optional[Notification]:
        try:
            if len(row) < 14:
                return None
            
            return Notification(
                id=row[0],
                client_id=row[1],
                type=NotificationType(row[2]),
                title=row[3],
                message=row[4],
                status=NotificationStatus(row[5]),
                priority=NotificationPriority(row[6]),
                channel=NotificationChannel(row[7]),
                created_at=datetime.fromisoformat(row[8]) if row[8] else datetime.utcnow(),
                scheduled_at=datetime.fromisoformat(row[9]) if row[9] else None,
                sent_at=datetime.fromisoformat(row[10]) if row[10] else None,
                delivered_at=datetime.fromisoformat(row[11]) if row[11] else None,
                failed_at=datetime.fromisoformat(row[12]) if row[12] else None,
                retry_count=int(row[13]) if row[13] else 0
            )
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing notification row: {e}", row=row)
            return None

    async def _find_row_num(self, notification_id: str) -> Optional[int]:
        try:
            ids_data = await self.sheets_client.read_range("A:A", self.SHEET_NAME)
            for i, row_data in enumerate(ids_data, 1):
                if row_data and row_data[0] == notification_id:
                    return i
            return None
        except GoogleSheetsError:
            return None

    async def save_notification(self, data):  # type: ignore[override]
        """Сохранить уведомление в Google Sheets."""
        from ..models.notification import NotificationCreateData  # локальный импорт для избежания циклов

        if not isinstance(data, NotificationCreateData):
            # Если передали готовый объект Notification, переводим к CreateData
            create_data = data  # type: ignore
        else:
            create_data = data

        await self._ensure_headers()

        # Создаём модель Notification из входных данных
        notification = Notification(
            client_id=create_data.client_id,
            type=create_data.type,
            title=create_data.title,
            message=create_data.message,
            priority=create_data.priority,
            scheduled_at=create_data.scheduled_at,
            metadata=create_data.metadata,
            channel=create_data.channel,
        )

        try:
            await self.sheets_client.append_rows([self._to_row(notification)], self.SHEET_NAME)
            logger.info(
                f"Notification {notification.id} saved for client {notification.client_id}")
            return notification
        except GoogleSheetsError as e:
            logger.error(f"Failed to save notification: {e}")
            raise

    async def get_notification_by_id(self, notification_id: str) -> Optional[Notification]:
        row_num = await self._find_row_num(notification_id)
        if not row_num:
            return None
            
        try:
            data = await self.sheets_client.read_range(f"A{row_num}:N{row_num}", self.SHEET_NAME)
            if not data or not data[0]:
                return None
            return self._from_row(data[0])
        except GoogleSheetsError as e:
            logger.error(f"Failed to get notification {notification_id}: {e}")
            return None

    async def update_notification_status(self, notification_id: str, status: NotificationStatus) -> bool:
        row_num = await self._find_row_num(notification_id)
        if not row_num:
            return False
            
        try:
            await self.sheets_client.write_range(f"F{row_num}", [[status.value]], self.SHEET_NAME)
            if status == NotificationStatus.SENT:
                await self.sheets_client.write_range(f"K{row_num}", [[datetime.utcnow().isoformat()]], self.SHEET_NAME)
            logger.info(f"Notification {notification_id} status updated to {status.value}")
            return True
        except GoogleSheetsError as e:
            logger.error(f"Failed to update notification {notification_id} status: {e}")
            return False

    async def get_pending_notifications(self) -> List[Notification]:
        try:
            all_data = await self.sheets_client.read_range("A2:N", self.SHEET_NAME)
            pending = []
            now = datetime.utcnow()
            for row in all_data:
                if row and len(row) > 5 and row[5] == NotificationStatus.PENDING.value:
                    notif = self._from_row(row)
                    if notif and (not notif.scheduled_at or notif.scheduled_at <= now):
                        pending.append(notif)
            return pending
        except GoogleSheetsError as e:
            logger.error(f"Failed to get pending notifications: {e}")
            return []

    # --- Реализация остальных методов протокола ---

    async def get_notifications_by_client_id(self, client_id: str, limit: Optional[int] = None, offset: Optional[int] = None):  # type: ignore[override]
        notifications = [n for n in await self.list_notifications() if n.client_id == client_id]
        if offset:
            notifications = notifications[offset:]
        if limit:
            notifications = notifications[:limit]
        return notifications

    async def get_notifications_by_status(self, status: NotificationStatus):  # type: ignore[override]
        return [n for n in await self.list_notifications() if n.status == status]

    async def get_notifications_by_type(self, notification_type):  # type: ignore[override]
        from ..models.notification import NotificationType
        if isinstance(notification_type, str):
            notification_type = NotificationType(notification_type)
        return [n for n in await self.list_notifications() if n.type == notification_type]

    async def get_notifications_by_priority(self, priority):  # type: ignore[override]
        from ..models.notification import NotificationPriority
        if isinstance(priority, str):
            priority = NotificationPriority(priority)
        return [n for n in await self.list_notifications() if n.priority == priority]

    async def get_scheduled_notifications(self, before_time: datetime):  # type: ignore[override]
        return [n for n in await self.list_notifications() if n.scheduled_at and n.scheduled_at <= before_time and n.status == NotificationStatus.PENDING]

    async def get_failed_notifications_for_retry(self):  # type: ignore[override]
        return [n for n in await self.list_notifications() if n.status == NotificationStatus.FAILED and n.retry_count < n.max_retries]

    async def update_notification(self, notification_id: str, data):  # type: ignore[override]
        from ..models.notification import NotificationUpdateData
        if not isinstance(data, NotificationUpdateData):
            logger.warning("update_notification получил не NotificationUpdateData")
            return None

        row_num = await self._find_row_num(notification_id)
        if not row_num:
            return None

        # Прочитаем текущую строку
        try:
            raw_row = await self.sheets_client.read_range(f"A{row_num}:N{row_num}", self.SHEET_NAME)
            if not raw_row or not raw_row[0]:
                return None
            notif = self._from_row(raw_row[0])
            if not notif:
                return None

            # Обновляем поля
            if data.status is not None:
                notif.status = data.status
            if data.sent_at is not None:
                notif.sent_at = data.sent_at
            if data.delivered_at is not None:
                notif.delivered_at = data.delivered_at
            if data.failed_at is not None:
                notif.failed_at = data.failed_at
            if data.telegram_message_id is not None:
                notif.telegram_message_id = data.telegram_message_id
            if data.retry_count is not None:
                notif.retry_count = data.retry_count
            if data.channel is not None:
                notif.channel = data.channel

            notif.updated_at = data.updated_at or datetime.utcnow()

            # Пишем обратно
            await self.sheets_client.write_range(f"A{row_num}:N{row_num}", [self._to_row(notif)], self.SHEET_NAME)
            return notif
        except GoogleSheetsError as e:
            logger.error(f"Failed to update notification {notification_id}: {e}")
            return None

    async def delete_notification(self, notification_id: str):  # type: ignore[override]
        from ..models.notification import NotificationUpdateData
        upd = NotificationUpdateData(status=NotificationStatus.CANCELLED, updated_at=datetime.utcnow())
        notif = await self.update_notification(notification_id, upd)
        return bool(notif)

    async def list_notifications(self, limit: Optional[int] = None, offset: Optional[int] = None):  # type: ignore[override]
        try:
            all_data = await self.sheets_client.read_range("A2:N", self.SHEET_NAME)
            notifications = [n for row in all_data if (n := self._from_row(row))]
            if offset:
                notifications = notifications[offset:]
            if limit:
                notifications = notifications[:limit]
            return notifications
        except GoogleSheetsError as e:
            logger.error(f"Failed to list notifications: {e}")
            return []

    async def count_notifications(self):  # type: ignore[override]
        return len(await self.list_notifications())

    async def count_notifications_by_client(self, client_id: str):  # type: ignore[override]
        return len(await self.get_notifications_by_client_id(client_id))

    async def count_notifications_by_status(self, status: NotificationStatus):  # type: ignore[override]
        return len(await self.get_notifications_by_status(status))

    async def get_notifications_created_between(self, start_time: datetime, end_time: datetime):  # type: ignore[override]
        return [n for n in await self.list_notifications() if start_time <= n.created_at <= end_time]

    async def cleanup_old_notifications(self, older_than: datetime):  # type: ignore[override]
        # Удаляем (мягко) уведомления созданные раньше указанной даты
        notifications = await self.list_notifications()
        count = 0
        for n in notifications:
            if n.created_at < older_than:
                await self.delete_notification(n.id)
                count += 1
        return count 