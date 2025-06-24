"""
📊 Протокол для сервиса аналитики
"""
from typing import Protocol, Dict, Any

class AnalyticsServiceProtocol(Protocol):
    """
    Протокол, определяющий интерфейс для сервиса аналитики.
    """
    
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Получение ключевых метрик для дашборда.
        """
        ...

    async def get_overview_analytics(self, period: str) -> Dict[str, Any]:
        """
        Получение общей аналитики за период.
        """
        ... 