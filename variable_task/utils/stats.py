import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import pandas as pd
from database import get_session, close_session
from models.models import Habit, Progress
from config import CHART_COLORS, CHART_STYLE, STATS_DIR
import os

# Установка стиля графиков
plt.style.use(CHART_STYLE)

def generate_weekly_progress(habit_id: int) -> str:
    """Генерация графика прогресса за неделю"""
    session = get_session()
    try:
        habit = session.query(Habit).get(habit_id)
        if not habit:
            return None

        # Получаем данные за последние 7 дней
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=6)
        
        progress_data = session.query(Progress).filter(
            Progress.habit_id == habit_id,
            Progress.date >= start_date,
            Progress.date <= end_date
        ).all()

        # Создаем DataFrame
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        data = []
        for date in dates:
            day_progress = next(
                (p for p in progress_data if p.date.date() == date.date()),
                None
            )
            data.append({
                'date': date,
                'completed': day_progress.completed if day_progress else False,
                'skipped': day_progress.skipped if day_progress else False
            })
        
        df = pd.DataFrame(data)

        # Создаем график
        plt.figure(figsize=(10, 6))
        plt.bar(
            df['date'],
            df['completed'].astype(int),
            color=CHART_COLORS[0],
            label='Выполнено'
        )
        plt.bar(
            df['date'],
            df['skipped'].astype(int),
            color=CHART_COLORS[2],
            label='Пропущено'
        )

        plt.title(f'Прогресс привычки «{habit.name}» за неделю')
        plt.xlabel('Дата')
        plt.ylabel('Статус')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Сохраняем график
        filename = f'weekly_progress_{habit_id}_{datetime.now().strftime("%Y%m%d")}.png'
        filepath = os.path.join(STATS_DIR, filename)
        plt.savefig(filepath)
        plt.close()

        return filepath
    finally:
        close_session()

def generate_completion_rate(habit_id: int) -> str:
    """Генерация круговой диаграммы процента выполнения"""
    session = get_session()
    try:
        habit = session.query(Habit).get(habit_id)
        if not habit:
            return None

        # Получаем статистику
        total = session.query(Progress).filter(
            Progress.habit_id == habit_id
        ).count()
        
        completed = session.query(Progress).filter(
            Progress.habit_id == habit_id,
            Progress.completed == True
        ).count()
        
        skipped = session.query(Progress).filter(
            Progress.habit_id == habit_id,
            Progress.skipped == True
        ).count()
        
        missed = total - completed - skipped

        # Создаем круговую диаграмму
        plt.figure(figsize=(8, 8))
        plt.pie(
            [completed, skipped, missed],
            labels=['Выполнено', 'Пропущено', 'Пропущено без отметки'],
            colors=CHART_COLORS[:3],
            autopct='%1.1f%%'
        )
        plt.title(f'Статистика выполнения привычки «{habit.name}»')

        # Сохраняем график
        filename = f'completion_rate_{habit_id}_{datetime.now().strftime("%Y%m%d")}.png'
        filepath = os.path.join(STATS_DIR, filename)
        plt.savefig(filepath)
        plt.close()

        return filepath
    finally:
        close_session()

def get_weekly_report(habit_id: int) -> str:
    """Генерация текстового отчета за неделю"""
    session = get_session()
    try:
        habit = session.query(Habit).get(habit_id)
        if not habit:
            return None

        # Получаем данные за последние 7 дней
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=6)
        
        progress_data = session.query(Progress).filter(
            Progress.habit_id == habit_id,
            Progress.date >= start_date,
            Progress.date <= end_date
        ).all()

        completed = sum(1 for p in progress_data if p.completed)
        skipped = sum(1 for p in progress_data if p.skipped)
        missed = 7 - completed - skipped

        report = (
            f"📊 Еженедельный отчет по привычке «{habit.name}»\n\n"
            f"Выполнено: {completed} дней\n"
            f"Пропущено: {skipped} дней\n"
            f"Пропущено без отметки: {missed} дней\n\n"
        )

        if completed >= 5:
            report += "🎉 Отличная работа! Вы на правильном пути!"
        elif completed >= 3:
            report += "👍 Хороший результат! Продолжайте в том же духе!"
        else:
            report += "💪 Не сдавайтесь! Каждый день - новая возможность!"

        return report
    finally:
        close_session() 