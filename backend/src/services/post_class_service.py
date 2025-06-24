"""
🎯 Сервис post-class автоматизации

Управляет автоматическими процессами после завершения занятий:
- Отправка благодарностей и обратной связи
- Сбор отзывов о занятии
- Предложения следующих занятий
- Мотивационные сообщения
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from ..models.booking import Booking, BookingStatus
from ..models.feedback import Feedback, FeedbackCreateData, FeedbackType
from ..models.client import Client
from ..models.subscription import Subscription
from ..models.notification import NotificationType
from ..services.protocols.client_service import ClientServiceProtocol
from ..services.protocols.subscription_service import SubscriptionServiceProtocol
from ..services.protocols.notification_service import NotificationServiceProtocol

logger = logging.getLogger(__name__)


class PostClassService:
    """
    Сервис автоматизации после занятий.
    
    Обеспечивает:
    - Автоматические уведомления после занятий
    - Сбор обратной связи
    - Предложения следующих занятий
    - Мотивационные сообщения
    - Аналитику посещаемости
    """
    
    def __init__(
        self,
        client_service: ClientServiceProtocol,
        subscription_service: SubscriptionServiceProtocol,
        notification_service: NotificationServiceProtocol
    ):
        """
        Инициализация сервиса post-class автоматизации.
        
        Args:
            client_service: Сервис клиентов
            subscription_service: Сервис абонементов
            notification_service: Сервис уведомлений
        """
        self._client_service = client_service
        self._subscription_service = subscription_service
        self._notification_service = notification_service
        
        logger.info("PostClassService инициализирован")
    
    async def process_completed_class(self, booking: Booking) -> Dict[str, Any]:
        """
        Обработать завершенное занятие.
        
        Args:
            booking: Запись на занятие со статусом ATTENDED
            
        Returns:
            Результат обработки с деталями отправленных уведомлений
        """
        if booking.status != BookingStatus.ATTENDED:
            logger.warning(f"Попытка обработать занятие {booking.id} со статусом {booking.status}")
            return {"success": False, "error": "Занятие не помечено как посещенное"}
        
        logger.info(f"Обработка завершенного занятия {booking.id} для клиента {booking.client_id}")
        
        try:
            # Получаем данные клиента и абонемента
            client = await self._client_service.get_client(booking.client_id)
            subscription = None
            if booking.subscription_id:
                subscription = await self._subscription_service.get_subscription(booking.subscription_id)
            
            results = {
                "booking_id": booking.id,
                "client_id": booking.client_id,
                "processed_at": datetime.now().isoformat(),
                "actions": []
            }
            
            # 1. Отправляем благодарность за посещение
            thank_you_sent = await self._send_thank_you_message(client, booking)
            results["actions"].append({
                "action": "thank_you_message",
                "success": thank_you_sent,
                "timestamp": datetime.now().isoformat()
            })
            
            # 2. Запрашиваем обратную связь (с задержкой 30 минут)
            feedback_scheduled = await self._schedule_feedback_request(client, booking)
            results["actions"].append({
                "action": "feedback_request_scheduled",
                "success": feedback_scheduled,
                "timestamp": datetime.now().isoformat()
            })
            
            # 3. Отправляем статистику прогресса (если есть абонемент)
            if subscription:
                progress_sent = await self._send_progress_update(client, subscription, booking)
                results["actions"].append({
                    "action": "progress_update",
                    "success": progress_sent,
                    "timestamp": datetime.now().isoformat()
                })
            
            # 4. Предлагаем следующие занятия
            recommendations_sent = await self._send_class_recommendations(client, booking)
            results["actions"].append({
                "action": "class_recommendations",
                "success": recommendations_sent,
                "timestamp": datetime.now().isoformat()
            })
            
            # 5. Проверяем достижения и отправляем поздравления
            achievements_sent = await self._check_and_send_achievements(client, booking)
            results["actions"].append({
                "action": "achievements_check",
                "success": achievements_sent,
                "timestamp": datetime.now().isoformat()
            })
            
            results["success"] = True
            logger.info(f"Обработка занятия {booking.id} завершена успешно")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при обработке завершенного занятия {booking.id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "booking_id": booking.id
            }
    
    async def _send_thank_you_message(self, client: Client, booking: Booking) -> bool:
        """Отправить благодарность за посещение занятия."""
        try:
            # Определяем время дня для персонализации
            hour = booking.class_date.hour
            if hour < 12:
                time_greeting = "Доброе утро"
            elif hour < 18:
                time_greeting = "Добрый день"
            else:
                time_greeting = "Добрый вечер"
            
            # Персонализированные сообщения в зависимости от типа занятия
            class_messages = {
                'хатха': 'Надеемся, вы почувствовали гармонию и спокойствие! 🧘‍♀️',
                'виньяса': 'Какой прекрасный поток энергии! Вы были великолепны! 💫',
                'аштанга': 'Впечатляющая практика! Ваша сила и выносливость растут! 💪',
                'инь': 'Глубокое расслабление достигнуто! Наслаждайтесь этим состоянием! 🌸',
                'йога-нидра': 'Какое прекрасное путешествие в мир релаксации! ✨',
                'кундалини': 'Энергия пробуждена! Чувствуете ли вы эту силу внутри? ⚡',
                'пранаяма': 'Дыхание - это жизнь! Прекрасная работа с энергией! 🌬️'
            }
            
            class_specific = class_messages.get(booking.class_type.lower(), 'Отличная практика!')
            
            await self._notification_service.send_immediate_notification(
                client_id=client.id,
                notification_type=NotificationType.GENERAL_INFO,
                template_data={
                    'client_name': client.name,
                    'time_greeting': time_greeting,
                    'class_type': booking.class_type,
                    'class_specific_message': class_specific,
                    'class_date': booking.class_date.strftime('%d.%m.%Y в %H:%M')
                }
            )
            
            logger.info(f"Благодарность отправлена клиенту {client.id} за занятие {booking.id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки благодарности клиенту {client.id}: {e}")
            return False
    
    async def _schedule_feedback_request(self, client: Client, booking: Booking) -> bool:
        """Запланировать запрос обратной связи через 30 минут."""
        try:
            # Планируем отправку через 30 минут после занятия
            scheduled_time = datetime.now() + timedelta(minutes=30)
            
            await self._notification_service.create_notification_from_template(
                client_id=client.id,
                notification_type=NotificationType.GENERAL_INFO,
                template_data={
                    'client_name': client.name,
                    'class_type': booking.class_type,
                    'feedback_request': True,
                    'booking_id': booking.id
                },
                scheduled_at=scheduled_time
            )
            
            logger.info(f"Запрос обратной связи запланирован для клиента {client.id} на {scheduled_time}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка планирования запроса обратной связи для клиента {client.id}: {e}")
            return False
    
    async def _send_progress_update(self, client: Client, subscription: Subscription, booking: Booking) -> bool:
        """Отправить обновление прогресса по абонементу."""
        try:
            remaining_classes = subscription.total_classes - subscription.used_classes
            progress_percentage = (subscription.used_classes / subscription.total_classes) * 100
            
            # Разные сообщения в зависимости от прогресса
            if progress_percentage >= 80:
                progress_message = "Вы почти у цели! Осталось совсем немного! 🎯"
            elif progress_percentage >= 50:
                progress_message = "Отличный прогресс! Вы на полпути к завершению абонемента! 📈"
            elif progress_percentage >= 25:
                progress_message = "Прекрасное начало! Продолжайте в том же духе! 🌟"
            else:
                progress_message = "Добро пожаловать в вашу йога-практику! Впереди много интересного! 🚀"
            
            await self._notification_service.send_immediate_notification(
                client_id=client.id,
                notification_type=NotificationType.GENERAL_INFO,
                template_data={
                    'client_name': client.name,
                    'used_classes': subscription.used_classes,
                    'total_classes': subscription.total_classes,
                    'remaining_classes': remaining_classes,
                    'progress_percentage': round(progress_percentage, 1),
                    'progress_message': progress_message
                }
            )
            
            logger.info(f"Обновление прогресса отправлено клиенту {client.id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки обновления прогресса клиенту {client.id}: {e}")
            return False
    
    async def _send_class_recommendations(self, client: Client, booking: Booking) -> bool:
        """Отправить рекомендации следующих занятий."""
        try:
            # Логика рекомендаций на основе типа занятия
            recommendations = self._get_class_recommendations(booking.class_type)
            
            await self._notification_service.send_immediate_notification(
                client_id=client.id,
                notification_type=NotificationType.GENERAL_INFO,
                template_data={
                    'client_name': client.name,
                    'current_class_type': booking.class_type,
                    'recommendations': recommendations,
                    'next_week_schedule': self._get_next_week_schedule()
                }
            )
            
            logger.info(f"Рекомендации занятий отправлены клиенту {client.id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки рекомендаций клиенту {client.id}: {e}")
            return False
    
    async def _check_and_send_achievements(self, client: Client, booking: Booking) -> bool:
        """Проверить достижения и отправить поздравления."""
        try:
            # Получаем статистику клиента (это будет реализовано позже)
            # Пока отправляем мотивационное сообщение
            
            motivational_messages = [
                "Каждое занятие - это шаг к лучшей версии себя! 🌟",
                "Ваша практика вдохновляет! Продолжайте развиваться! 💫",
                "Йога - это путешествие, а не пункт назначения. Наслаждайтесь процессом! 🧘‍♀️",
                "Сегодня вы стали сильнее, чем вчера! 💪",
                "Ваша преданность практике восхищает! 🙏"
            ]
            
            import random
            selected_message = random.choice(motivational_messages)
            
            await self._notification_service.send_immediate_notification(
                client_id=client.id,
                notification_type=NotificationType.GENERAL_INFO,
                template_data={
                    'client_name': client.name,
                    'motivational_message': selected_message,
                    'class_type': booking.class_type
                }
            )
            
            logger.info(f"Мотивационное сообщение отправлено клиенту {client.id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки мотивационного сообщения клиенту {client.id}: {e}")
            return False
    
    def _get_class_recommendations(self, current_class_type: str) -> List[str]:
        """Получить рекомендации занятий на основе текущего типа."""
        recommendations_map = {
            'хатха': ['Виньяса-флоу для развития динамики', 'Йога-нидра для глубокого расслабления'],
            'виньяса': ['Хатха для укрепления основ', 'Аштанга для повышения силы'],
            'аштанга': ['Инь-йога для восстановления', 'Пранаяма для работы с дыханием'],
            'инь': ['Хатха для активной практики', 'Медитация для углубления осознанности'],
            'йога-нидра': ['Хатха для физической активности', 'Кундалини для энергетической работы'],
            'кундалини': ['Виньяса для динамичной практики', 'Медитация для интеграции опыта'],
            'пранаяма': ['Хатха для физической практики', 'Медитация для углубления концентрации']
        }
        
        return recommendations_map.get(current_class_type.lower(), [
            'Хатха-йога для основ',
            'Виньяса-флоу для динамики'
        ])
    
    def _get_next_week_schedule(self) -> Dict[str, List[str]]:
        """Получить расписание на следующую неделю."""
        # Упрощенное расписание (в реальности будет браться из системы расписания)
        return {
            'Понедельник': ['09:00 Хатха-йога', '19:00 Виньяса-флоу'],
            'Вторник': ['10:00 Аштанга', '18:30 Йога-нидра'],
            'Среда': ['09:30 Виньяса-флоу', '19:00 Инь-йога'],
            'Четверг': ['10:00 Хатха-йога', '18:00 Кундалини'],
            'Пятница': ['09:00 Пранаяма', '19:30 Виньяса-флоу'],
            'Суббота': ['10:00 Семейная йога', '16:00 Хатха-йога'],
            'Воскресенье': ['10:30 Медитативная практика', '18:00 Инь-йога']
        }
    
    async def process_missed_class(self, booking: Booking) -> Dict[str, Any]:
        """
        Обработать пропущенное занятие.
        
        Args:
            booking: Запись на занятие со статусом MISSED
            
        Returns:
            Результат обработки
        """
        if booking.status != BookingStatus.MISSED:
            logger.warning(f"Попытка обработать пропуск занятия {booking.id} со статусом {booking.status}")
            return {"success": False, "error": "Занятие не помечено как пропущенное"}
        
        logger.info(f"Обработка пропущенного занятия {booking.id} для клиента {booking.client_id}")
        
        try:
            client = await self._client_service.get_client(booking.client_id)
            
            # Отправляем поддерживающее сообщение
            await self._notification_service.send_immediate_notification(
                client_id=client.id,
                notification_type=NotificationType.GENERAL_INFO,
                template_data={
                    'client_name': client.name,
                    'missed_class': True,
                    'class_type': booking.class_type,
                    'class_date': booking.class_date.strftime('%d.%m.%Y в %H:%M'),
                    'next_opportunities': self._get_next_week_schedule()
                }
            )
            
            logger.info(f"Сообщение о пропуске отправлено клиенту {client.id}")
            return {
                "success": True,
                "booking_id": booking.id,
                "client_id": booking.client_id,
                "action": "missed_class_message_sent"
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке пропущенного занятия {booking.id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "booking_id": booking.id
            }
    
    async def send_daily_motivation(self, client_ids: Optional[List[str]] = None) -> int:
        """
        Отправить ежедневную мотивацию активным клиентам.
        
        Args:
            client_ids: Список ID клиентов (если None, отправляется всем активным)
            
        Returns:
            Количество отправленных сообщений
        """
        try:
            if client_ids is None:
                clients = await self._client_service.get_active_clients()
                client_ids = [client.id for client in clients]
            
            sent_count = 0
            daily_tips = [
                "🌅 Начните день с глубокого дыхания - это зарядит вас энергией на весь день!",
                "🧘‍♀️ Помните: йога - это не о совершенстве, а о прогрессе. Каждый день - новая возможность!",
                "💫 Ваше тело способно на удивительные вещи. Доверьтесь ему и слушайте его сигналы.",
                "🌸 Практика йоги - это подарок, который вы делаете себе. Цените это время.",
                "⚡ Сила не в том, чтобы удержать позу, а в том, чтобы найти спокойствие в движении.",
                "🙏 Благодарность - это йога сердца. За что вы благодарны сегодня?",
                "🌟 Каждое занятие приближает вас к лучшей версии себя. Продолжайте путь!"
            ]
            
            import random
            selected_tip = random.choice(daily_tips)
            
            for client_id in client_ids:
                try:
                    client = await self._client_service.get_client(client_id)
                    
                    await self._notification_service.send_immediate_notification(
                        client_id=client.id,
                        notification_type=NotificationType.GENERAL_INFO,
                        template_data={
                            'client_name': client.name,
                            'daily_motivation': True,
                            'tip_message': selected_tip,
                            'today_schedule': self._get_today_schedule()
                        }
                    )
                    
                    sent_count += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки мотивации клиенту {client_id}: {e}")
                    continue
            
            logger.info(f"Ежедневная мотивация отправлена {sent_count} клиентам")
            return sent_count
            
        except Exception as e:
            logger.error(f"Ошибка отправки ежедневной мотивации: {e}")
            return 0
    
    def _get_today_schedule(self) -> List[str]:
        """Получить расписание на сегодня."""
        today = datetime.now().strftime('%A')
        schedule_map = {
            'Monday': ['09:00 Хатха-йога', '19:00 Виньяса-флоу'],
            'Tuesday': ['10:00 Аштанга', '18:30 Йога-нидра'],
            'Wednesday': ['09:30 Виньяса-флоу', '19:00 Инь-йога'],
            'Thursday': ['10:00 Хатха-йога', '18:00 Кундалини'],
            'Friday': ['09:00 Пранаяма', '19:30 Виньяса-флоу'],
            'Saturday': ['10:00 Семейная йога', '16:00 Хатха-йога'],
            'Sunday': ['10:30 Медитативная практика', '18:00 Инь-йога']
        }
        
        return schedule_map.get(today, ['Расписание уточняется']) 