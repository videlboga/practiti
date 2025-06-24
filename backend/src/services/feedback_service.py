"""
💬 Сервис управления обратной связью

Управляет сбором, обработкой и анализом обратной связи от клиентов:
- Создание запросов на обратную связь
- Обработка полученных отзывов
- Аналитика и отчеты
- Интеграция с уведомлениями
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from ..models.feedback import (
    Feedback, FeedbackCreateData, FeedbackUpdateData, 
    FeedbackType, FeedbackStatus, FeedbackSummary
)
from ..models.client import Client
from ..models.booking import Booking
from ..models.notification import NotificationType
from ..services.protocols.notification_service import NotificationServiceProtocol

logger = logging.getLogger(__name__)


class FeedbackService:
    """
    Сервис управления обратной связью.
    
    Обеспечивает:
    - Создание и управление запросами обратной связи
    - Обработка полученных отзывов
    - Аналитика и статистика
    - Интеграция с системой уведомлений
    """
    
    def __init__(self, notification_service: NotificationServiceProtocol):
        """
        Инициализация сервиса обратной связи.
        
        Args:
            notification_service: Сервис уведомлений
        """
        self._notification_service = notification_service
        self._feedback_storage: Dict[str, Feedback] = {}  # Временное хранилище
        
        logger.info("FeedbackService инициализирован")
    
    async def create_feedback_request(
        self, 
        client: Client, 
        booking: Booking,
        feedback_type: FeedbackType = FeedbackType.POST_CLASS
    ) -> Feedback:
        """
        Создать запрос на обратную связь.
        
        Args:
            client: Клиент
            booking: Запись на занятие
            feedback_type: Тип обратной связи
            
        Returns:
            Созданный объект обратной связи
        """
        try:
            feedback_data = FeedbackCreateData(
                client_id=client.id,
                type=feedback_type,
                booking_id=booking.id,
                subscription_id=booking.subscription_id,
                metadata={
                    'class_type': booking.class_type,
                    'class_date': booking.class_date.isoformat(),
                    'teacher_name': booking.teacher_name
                }
            )
            
            feedback = Feedback(
                client_id=feedback_data.client_id,
                type=feedback_data.type,
                booking_id=feedback_data.booking_id,
                subscription_id=feedback_data.subscription_id,
                metadata=feedback_data.metadata
            )
            
            # Сохраняем в временное хранилище
            self._feedback_storage[feedback.id] = feedback
            
            logger.info(f"Создан запрос обратной связи {feedback.id} для клиента {client.id}")
            return feedback
            
        except Exception as e:
            logger.error(f"Ошибка создания запроса обратной связи для клиента {client.id}: {e}")
            raise
    
    async def send_feedback_request(self, feedback: Feedback, client: Client) -> bool:
        """
        Отправить запрос обратной связи клиенту.
        
        Args:
            feedback: Объект обратной связи
            client: Клиент
            
        Returns:
            True если запрос отправлен успешно
        """
        try:
            # Формируем персонализированное сообщение
            if feedback.type == FeedbackType.POST_CLASS:
                message_template = self._get_post_class_feedback_template(feedback, client)
            else:
                message_template = self._get_general_feedback_template(feedback, client)
            
            # Отправляем уведомление
            await self._notification_service.send_immediate_notification(
                client_id=client.id,
                notification_type=NotificationType.GENERAL_INFO,
                template_data=message_template
            )
            
            logger.info(f"Запрос обратной связи {feedback.id} отправлен клиенту {client.id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки запроса обратной связи {feedback.id}: {e}")
            return False
    
    def _get_post_class_feedback_template(self, feedback: Feedback, client: Client) -> Dict[str, Any]:
        """Получить шаблон запроса обратной связи после занятия."""
        class_type = feedback.metadata.get('class_type', 'занятие')
        
        return {
            'client_name': client.name,
            'feedback_request': True,
            'feedback_type': 'post_class',
            'class_type': class_type,
            'feedback_id': feedback.id,
            'message': f"""🙏 Спасибо за участие в {class_type}!

Ваше мнение очень важно для нас. Пожалуйста, поделитесь впечатлениями:

⭐ Как бы вы оценили занятие? (1-5 звезд)
💭 Что вам больше всего понравилось?
🎯 Подходил ли уровень сложности?
📝 Есть ли предложения по улучшению?

Ваши отзывы помогают нам становиться лучше! ✨"""
        }
    
    def _get_general_feedback_template(self, feedback: Feedback, client: Client) -> Dict[str, Any]:
        """Получить шаблон общего запроса обратной связи."""
        return {
            'client_name': client.name,
            'feedback_request': True,
            'feedback_type': 'general',
            'feedback_id': feedback.id,
            'message': f"""💬 Поделитесь своими впечатлениями!

Мы ценим ваше мнение о нашей йога-студии:

⭐ Как бы вы оценили наши услуги?
🏢 Что вам нравится в студии?
🔄 Что можно улучшить?
👥 Порекомендовали бы нас друзьям?

Ваши отзывы помогают нам развиваться! 🌟"""
        }
    
    async def submit_feedback(self, feedback_id: str, update_data: FeedbackUpdateData) -> Feedback:
        """
        Принять обратную связь от клиента.
        
        Args:
            feedback_id: ID обратной связи
            update_data: Данные обратной связи
            
        Returns:
            Обновленный объект обратной связи
        """
        try:
            feedback = self._feedback_storage.get(feedback_id)
            if not feedback:
                raise ValueError(f"Обратная связь {feedback_id} не найдена")
            
            # Обновляем данные
            if update_data.rating is not None:
                feedback.rating = update_data.rating
            if update_data.comment is not None:
                feedback.comment = update_data.comment
            if update_data.class_rating is not None:
                feedback.class_rating = update_data.class_rating
            if update_data.teacher_rating is not None:
                feedback.teacher_rating = update_data.teacher_rating
            if update_data.studio_rating is not None:
                feedback.studio_rating = update_data.studio_rating
            if update_data.would_recommend is not None:
                feedback.would_recommend = update_data.would_recommend
            if update_data.difficulty_level is not None:
                feedback.difficulty_level = update_data.difficulty_level
            if update_data.favorite_part is not None:
                feedback.favorite_part = update_data.favorite_part
            if update_data.improvement_suggestions is not None:
                feedback.improvement_suggestions = update_data.improvement_suggestions
            
            # Обновляем статус и время
            feedback.status = FeedbackStatus.SUBMITTED
            feedback.submitted_at = datetime.now()
            
            # Сохраняем обновления
            self._feedback_storage[feedback_id] = feedback
            
            logger.info(f"Обратная связь {feedback_id} получена и обработана")
            return feedback
            
        except Exception as e:
            logger.error(f"Ошибка обработки обратной связи {feedback_id}: {e}")
            raise
    
    async def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """
        Получить обратную связь по ID.
        
        Args:
            feedback_id: ID обратной связи
            
        Returns:
            Объект обратной связи или None
        """
        return self._feedback_storage.get(feedback_id)
    
    async def get_client_feedback(self, client_id: str) -> List[Feedback]:
        """
        Получить всю обратную связь клиента.
        
        Args:
            client_id: ID клиента
            
        Returns:
            Список обратной связи клиента
        """
        return [
            feedback for feedback in self._feedback_storage.values()
            if feedback.client_id == client_id
        ]
    
    async def get_booking_feedback(self, booking_id: str) -> Optional[Feedback]:
        """
        Получить обратную связь по занятию.
        
        Args:
            booking_id: ID записи на занятие
            
        Returns:
            Обратная связь по занятию или None
        """
        for feedback in self._feedback_storage.values():
            if feedback.booking_id == booking_id:
                return feedback
        return None
    
    async def get_feedback_summary(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        feedback_type: Optional[FeedbackType] = None
    ) -> FeedbackSummary:
        """
        Получить сводку по обратной связи.
        
        Args:
            start_date: Начальная дата периода
            end_date: Конечная дата периода
            feedback_type: Тип обратной связи для фильтрации
            
        Returns:
            Сводка по обратной связи
        """
        try:
            # Фильтруем обратную связь
            filtered_feedback = []
            for feedback in self._feedback_storage.values():
                if feedback.status != FeedbackStatus.SUBMITTED:
                    continue
                
                if start_date and feedback.submitted_at and feedback.submitted_at < start_date:
                    continue
                
                if end_date and feedback.submitted_at and feedback.submitted_at > end_date:
                    continue
                
                if feedback_type and feedback.type != feedback_type:
                    continue
                
                filtered_feedback.append(feedback)
            
            # Вычисляем статистику
            total_feedback = len(filtered_feedback)
            
            if total_feedback == 0:
                return FeedbackSummary(
                    total_feedback=0,
                    average_rating=None,
                    positive_feedback_percentage=0.0,
                    period_start=start_date or datetime.now(),
                    period_end=end_date or datetime.now()
                )
            
            # Средняя оценка
            ratings = [f.overall_rating for f in filtered_feedback if f.overall_rating is not None]
            average_rating = sum(ratings) / len(ratings) if ratings else None
            
            # Процент положительных отзывов
            positive_count = sum(1 for f in filtered_feedback if f.is_positive)
            positive_percentage = (positive_count / total_feedback) * 100
            
            # Распределение оценок
            rating_distribution = {}
            for feedback in filtered_feedback:
                if feedback.rating is not None:
                    rating_distribution[feedback.rating] = rating_distribution.get(feedback.rating, 0) + 1
            
            # Подсчет по типам
            post_class_count = sum(1 for f in filtered_feedback if f.type == FeedbackType.POST_CLASS)
            general_count = sum(1 for f in filtered_feedback if f.type == FeedbackType.GENERAL)
            
            return FeedbackSummary(
                total_feedback=total_feedback,
                average_rating=average_rating,
                positive_feedback_percentage=positive_percentage,
                rating_distribution=rating_distribution,
                post_class_count=post_class_count,
                general_count=general_count,
                period_start=start_date or datetime.now() - timedelta(days=30),
                period_end=end_date or datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания сводки обратной связи: {e}")
            raise
