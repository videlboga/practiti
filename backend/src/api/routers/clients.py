"""
👥 API роутер для управления клиентами

CRUD операции для клиентов йога-студии.
Принцип CyberKitty: простота превыше всего.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging
import math

from ..models import (
    ClientCreateRequest, ClientUpdateRequest, ClientResponse, ClientSearchRequest,
    APIResponse, PaginationParams, PaginatedResponse, SubscriptionResponse
)
from ...services.protocols.client_service import ClientServiceProtocol
from ...models.client import ClientStatus
from ...utils.exceptions import BusinessLogicError, ValidationError
from functools import lru_cache
from ...services.client_service import ClientService
from ...config.settings import settings
from .subscriptions import _build_subscription_service
from ...services.protocols.subscription_service import SubscriptionServiceProtocol

logger = logging.getLogger(__name__)

router = APIRouter()


# Функции для DI
def _create_repository():
    """Создаёт конкретный репозиторий в зависимости от окружения."""
    if settings.environment == "testing":
        from ...repositories.in_memory_client_repository import InMemoryClientRepository
        return InMemoryClientRepository()
    else:
        from ...repositories.google_sheets_client_repository import GoogleSheetsClientRepository
        from ...integrations.google_sheets import GoogleSheetsClient
        return GoogleSheetsClientRepository(GoogleSheetsClient())


def _build_client_service() -> ClientServiceProtocol:
    """Фабрика, создающая singleton-экземпляр ClientService."""
    # Используем репозиторий в памяти для тестовой среды
    return ClientService(_create_repository())


@lru_cache(maxsize=1)
def _get_cached_client_service() -> ClientServiceProtocol:
    return _build_client_service()


async def get_client_service() -> ClientServiceProtocol:
    """Dependency-provider для FastAPI.

    В production-режиме используем кэш (singleton-сервис) для производительности.
    В testing-режиме кэш отключаем, чтобы каждый тест получал "свежий" инстанс
    и не возникало побочных эффектов из-за общего состояния между тестами.
    """

    if settings.environment == "testing":  # без кэша – изолированные тесты
        return _build_client_service()

    # для остальных окружений отдаём singleton
    return _get_cached_client_service()


@router.get("/", response_model=PaginatedResponse)
async def get_clients(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(20, ge=1, le=100, description="Количество в выдаче"),
    page_size: Optional[int] = Query(None, alias="pageSize", ge=1, le=100, description="Альтернативное имя параметра limit из фронтенда"),
    search: Optional[str] = Query(None, description="Поисковый запрос"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    client_service: ClientServiceProtocol = Depends(get_client_service)
) -> PaginatedResponse:
    """
    Получить список клиентов с пагинацией.
    
    Args:
        page: Номер страницы
        limit: Количество элементов на странице
        page_size: Альтернативное имя параметра limit из фронтенда
        search: Поисковый запрос
        status: Фильтр по статусу клиента
        client_service: Сервис клиентов
        
    Returns:
        Список клиентов с пагинацией
    """
    try:
        # Привязываем альтернативное имя параметра
        if page_size is not None:
            limit = page_size

        logger.info(f"Запрос списка клиентов: page={page}, limit={limit}, status={status}, search={search}")
        
        # Приводим статус к Enum, если передан и не пустая строка
        status_enum: Optional[ClientStatus] = None
        if status and str(status).strip():
            try:
                status_enum = ClientStatus(status)
            except ValueError:
                # Неизвестный статус – игнорируем фильтр
                logger.warning(f"Неизвестный статус клиента: {status}")

        # Получаем список клиентов
        if search and search.strip():
            clients = await client_service.search_clients(search.strip())
            # При необходимости фильтруем по статусу
            if status_enum:
                clients = [c for c in clients if c.status == status_enum]
        else:
            if status_enum:
                clients = await client_service.get_clients_by_status(status_enum)
            else:
                clients = await client_service.get_all_clients()
        
        # Пагинация
        total = len(clients)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_clients = clients[start_idx:end_idx]
        
        # Конвертируем в response модели
        client_responses = [
            ClientResponse.model_validate(client, from_attributes=True) for client in paginated_clients
        ]
        
        return PaginatedResponse(
            items=client_responses,
            total=total,
            page=page,
            limit=limit,
            pages=math.ceil(total / limit) if total > 0 else 1
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения списка клиентов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка клиентов")


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    client_service: ClientServiceProtocol = Depends(get_client_service)
) -> ClientResponse:
    """
    Получить клиента по ID.
    
    Args:
        client_id: ID клиента
        client_service: Сервис клиентов
        
    Returns:
        Данные клиента
    """
    try:
        logger.info(f"Запрос клиента: {client_id}")
        
        client = await client_service.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Клиент не найден")
        
        return ClientResponse.model_validate(client, from_attributes=True)
        
    except BusinessLogicError as e:
        logger.warning(f"Клиент не найден: {client_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка получения клиента {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения клиента")


@router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(
    request: ClientCreateRequest,
    client_service: ClientServiceProtocol = Depends(get_client_service)
) -> ClientResponse:
    """
    Создать нового клиента.
    
    Args:
        request: Данные для создания клиента
        client_service: Сервис клиентов
        
    Returns:
        Созданный клиент
    """
    try:
        logger.info(f"Создание клиента: {request.name}, {request.phone}")
        
        # Конвертируем request в модель создания
        from ...models.client import ClientCreateData
        
        create_data = ClientCreateData(
            name=request.name,
            phone=request.phone,
            telegram_id=request.telegram_id,
            yoga_experience=request.yoga_experience,
            intensity_preference=request.intensity_preference,
            time_preference=request.time_preference,
            age=request.age,
            injuries=request.injuries,
            goals=request.goals,
            how_found_us=request.how_found_us
        )
        
        client = await client_service.create_client(create_data)
        
        logger.info(f"Клиент создан: {client.id}")
        return ClientResponse.model_validate(client, from_attributes=True)
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка бизнес-логики при создании клиента: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Ошибка валидации при создании клиента: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка создания клиента: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания клиента")


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    request: ClientUpdateRequest,
    client_service: ClientServiceProtocol = Depends(get_client_service)
) -> ClientResponse:
    """
    Обновить данные клиента.
    
    Args:
        client_id: ID клиента
        request: Данные для обновления
        client_service: Сервис клиентов
        
    Returns:
        Обновленный клиент
    """
    try:
        logger.info(f"Обновление клиента: {client_id}")
        
        # Проверяем существование клиента
        existing_client = await client_service.get_client(client_id)
        if not existing_client:
            raise HTTPException(status_code=404, detail="Клиент не найден")
        
        # Конвертируем request в модель обновления
        from ...models.client import ClientUpdateData
        
        # Создаем словарь только с переданными полями
        update_data_dict = {}
        for field, value in request.dict(exclude_unset=True).items():
            if value is not None:
                update_data_dict[field] = value
        
        if not update_data_dict:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")
        
        update_data = ClientUpdateData(**update_data_dict)
        client = await client_service.update_client(client_id, update_data)
        
        logger.info(f"Клиент обновлен: {client_id}")
        return ClientResponse.model_validate(client, from_attributes=True)
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка бизнес-логики при обновлении клиента: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Ошибка валидации при обновлении клиента: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка обновления клиента {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления клиента")


@router.delete("/{client_id}", response_model=APIResponse)
async def delete_client(
    client_id: str,
    client_service: ClientServiceProtocol = Depends(get_client_service)
) -> APIResponse:
    """
    Удалить клиента (мягкое удаление).
    
    Args:
        client_id: ID клиента
        client_service: Сервис клиентов
        
    Returns:
        Результат операции
    """
    try:
        logger.info(f"Удаление клиента: {client_id}")
        
        await client_service.delete_client(client_id)
        
        logger.info(f"Клиент удален: {client_id}")
        return APIResponse(
            success=True,
            message=f"Клиент {client_id} успешно удален"
        )
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка при удалении клиента: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка удаления клиента {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления клиента")


@router.post("/search", response_model=PaginatedResponse)
async def search_clients(
    search_request: ClientSearchRequest,
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(20, ge=1, le=100, description="Количество на странице"),
    client_service: ClientServiceProtocol = Depends(get_client_service)
) -> PaginatedResponse:
    """
    Поиск клиентов по различным критериям.
    
    Args:
        search_request: Критерии поиска
        page: Номер страницы
        limit: Количество элементов на странице
        client_service: Сервис клиентов
        
    Returns:
        Результаты поиска с пагинацией
    """
    try:
        logger.info(f"Поиск клиентов: {search_request.dict()}")
        
        # Выполняем поиск
        clients = await client_service.search_clients(
            query=search_request.query,
            filters={
                "status": search_request.status,
                "yoga_experience": search_request.yoga_experience,
                "intensity_preference": search_request.intensity_preference,
                "time_preference": search_request.time_preference
            }
        )
        
        # Пагинация
        total = len(clients)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_clients = clients[start_idx:end_idx]
        
        # Конвертируем в response модели
        client_responses = [
            ClientResponse.model_validate(client, from_attributes=True) for client in paginated_clients
        ]
        
        return PaginatedResponse(
            items=client_responses,
            total=total,
            page=page,
            limit=limit,
            pages=math.ceil(total / limit) if total > 0 else 1
        )
        
    except Exception as e:
        logger.error(f"Ошибка поиска клиентов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка поиска клиентов")


@router.patch("/{client_id}/activate", response_model=ClientResponse)
async def activate_client(
    client_id: str,
    client_service: ClientServiceProtocol = Depends(get_client_service)
) -> ClientResponse:
    """
    Активировать клиента.
    
    Args:
        client_id: ID клиента
        client_service: Сервис клиентов
        
    Returns:
        Активированный клиент
    """
    try:
        logger.info(f"Активация клиента: {client_id}")
        
        client = await client_service.activate_client(client_id)
        
        logger.info(f"Клиент активирован: {client_id}")
        return ClientResponse.model_validate(client, from_attributes=True)
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка при активации клиента: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка активации клиента {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка активации клиента")


@router.patch("/{client_id}/deactivate", response_model=ClientResponse)
async def deactivate_client(
    client_id: str,
    client_service: ClientServiceProtocol = Depends(get_client_service)
) -> ClientResponse:
    """
    Деактивировать клиента.
    
    Args:
        client_id: ID клиента
        client_service: Сервис клиентов
        
    Returns:
        Деактивированный клиент
    """
    try:
        logger.info(f"Деактивация клиента: {client_id}")
        
        client = await client_service.deactivate_client(client_id)
        
        logger.info(f"Клиент деактивирован: {client_id}")
        return ClientResponse.model_validate(client, from_attributes=True)
        
    except BusinessLogicError as e:
        logger.warning(f"Ошибка при деактивации клиента: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка деактивации клиента {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка деактивации клиента")


@router.get("/{client_id}/subscriptions", response_model=List[SubscriptionResponse])
async def get_client_subscriptions(
    client_id: str,
    subscription_service: SubscriptionServiceProtocol = Depends(_build_subscription_service),
):
    """Получить абонементы конкретного клиента."""
    try:
        subs = await subscription_service.get_client_subscriptions(client_id)
        return [SubscriptionResponse.from_orm(s) for s in subs]
    except Exception as e:
        logger.error(f"Ошибка получения абонементов клиента {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения абонементов клиента") 