"""
🚀 FastAPI приложение для админ-панели Practiti

REST API для управления йога-студией.
Принцип CyberKitty: простота превыше всего.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from ..config.settings import settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Создание FastAPI приложения с настройками.
    
    Returns:
        Настроенное FastAPI приложение
    """
    app = FastAPI(
        title="Practiti Admin API",
        description="REST API для управления йога-студией Practiti",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # CORS middleware для фронтенда
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://localhost:5176",
        ],  # React / Vite dev server (порт может сдвигаться)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Глобальный обработчик ошибок
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc: Exception) -> JSONResponse:
        """Глобальный обработчик ошибок."""
        logger.error(f"Необработанная ошибка: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "Внутренняя ошибка сервера",
                "detail": str(exc) if settings.debug else None
            }
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """Проверка состояния API."""
        return {
            "status": "healthy",
            "service": "practiti-admin-api",
            "version": "1.0.0"
        }
    
    # Подключение роутеров
    from .routers import clients, subscriptions, notifications, analytics, bookings
    
    app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
    app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
    app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
    app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
    app.include_router(bookings.router, prefix="/api/v1", tags=["bookings"])
    
    # Временные алиасы без версии для обратной совместимости с фронтендом
    app.include_router(clients.router, prefix="/api/clients", tags=["clients-alias"])
    app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions-alias"])
    app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications-alias"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics-alias"])
    app.include_router(bookings.router, prefix="/api", tags=["bookings-alias"])
    
    # -----------------------------
    #  Алиас для метрик дашборда
    # -----------------------------

    from .routers.analytics import get_dashboard_metrics as _dashboard_metrics_handler

    # Фронтенд обращается к /api/dashboard/metrics, поэтому добавляем ручной маршрут
    app.add_api_route(
        path="/api/dashboard/metrics",
        endpoint=_dashboard_metrics_handler,
        methods=["GET"],
        tags=["analytics-alias"],
        name="dashboard-metrics-alias",
    )
    
    logger.info("FastAPI приложение создано")
    return app


# Создаем экземпляр приложения
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    ) 