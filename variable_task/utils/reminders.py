from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from database import get_session, close_session
from models.models import Habit, Progress
import json

class ReminderManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    def setup_reminders(self):
        """Настройка напоминаний для всех привычек"""
        session = get_session()
        try:
            habits = session.query(Habit).all()
            for habit in habits:
                reminder_times = json.loads(habit.reminder_times)
                for time in reminder_times:
                    hour, minute = map(int, time.split(':'))
                    self.scheduler.add_job(
                        self.send_reminder,
                        CronTrigger(hour=hour, minute=minute),
                        args=[habit.id],
                        id=f'habit_{habit.id}_{time}'
                    )
        finally:
            close_session()

    async def send_reminder(self, habit_id: int):
        """Отправка напоминания о привычке"""
        session = get_session()
        try:
            habit = session.query(Habit).get(habit_id)
            if not habit:
                return

            # Проверяем, выполнена ли уже привычка сегодня
            today = datetime.utcnow().date()
            progress = session.query(Progress).filter(
                Progress.habit_id == habit_id,
                Progress.date >= today,
                Progress.date < today + timedelta(days=1)
            ).first()

            if progress and progress.completed:
                return

            # Получаем статистику выполнения
            total_days = session.query(Progress).filter(
                Progress.habit_id == habit_id
            ).count()
            
            completed_days = session.query(Progress).filter(
                Progress.habit_id == habit_id,
                Progress.completed == True
            ).count()

            completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0

            message = (
                f"⏰ Напоминание о привычке «{habit.name}»!\n\n"
                f"Ваш прогресс: {completion_rate:.1f}%\n"
                f"Выполнено дней: {completed_days} из {total_days}\n\n"
                "Отметьте выполнение командой:\n"
                f"/done_{habit.id}"
            )

            await self.bot.send_message(
                chat_id=habit.user.telegram_id,
                text=message
            )
        finally:
            close_session()

    def update_reminder(self, habit_id: int, new_times: list):
        """Обновление времени напоминаний для привычки"""
        # Удаляем старые напоминания
        for job in self.scheduler.get_jobs():
            if job.id.startswith(f'habit_{habit_id}_'):
                job.remove()

        # Добавляем новые напоминания
        for time in new_times:
            hour, minute = map(int, time.split(':'))
            self.scheduler.add_job(
                self.send_reminder,
                CronTrigger(hour=hour, minute=minute),
                args=[habit_id],
                id=f'habit_{habit_id}_{time}'
            ) 