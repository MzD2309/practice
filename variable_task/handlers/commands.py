from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_session, close_session
from models.models import User, Habit, Progress, HabitType
from utils.stats import generate_weekly_progress, generate_completion_rate, get_weekly_report
import json

async def done_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /done для отметки выполнения привычки"""
    if not context.args:
        await update.message.reply_text(
            "Использование: /done <id_привычки>"
        )
        return

    habit_id = int(context.args[0])
    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("Сначала используйте команду /start")
            return

        habit = session.query(Habit).filter_by(id=habit_id, user_id=user.id).first()
        if not habit:
            await update.message.reply_text("Привычка не найдена")
            return

        # Проверяем, есть ли уже отметка на сегодня
        today = datetime.utcnow().date()
        progress = session.query(Progress).filter(
            Progress.habit_id == habit_id,
            Progress.date >= today,
            Progress.date < today + timedelta(days=1)
        ).first()

        if progress:
            progress.completed = True
            progress.skipped = False
        else:
            progress = Progress(
                habit_id=habit_id,
                completed=True,
                skipped=False
            )
            session.add(progress)

        session.commit()

        # Получаем статистику
        total_days = session.query(Progress).filter(
            Progress.habit_id == habit_id
        ).count()
        
        completed_days = session.query(Progress).filter(
            Progress.habit_id == habit_id,
            Progress.completed == True
        ).count()

        completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0

        await update.message.reply_text(
            f"✅ Привычка «{habit.name}» отмечена как выполненная!\n\n"
            f"Ваш прогресс: {completion_rate:.1f}%\n"
            f"Выполнено дней: {completed_days} из {total_days}"
        )
    finally:
        close_session()

async def skip_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /skip для пропуска привычки"""
    if not context.args:
        await update.message.reply_text(
            "Использование: /skip <id_привычки>"
        )
        return

    habit_id = int(context.args[0])
    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("Сначала используйте команду /start")
            return

        habit = session.query(Habit).filter_by(id=habit_id, user_id=user.id).first()
        if not habit:
            await update.message.reply_text("Привычка не найдена")
            return

        # Проверяем, есть ли уже отметка на сегодня
        today = datetime.utcnow().date()
        progress = session.query(Progress).filter(
            Progress.habit_id == habit_id,
            Progress.date >= today,
            Progress.date < today + timedelta(days=1)
        ).first()

        if progress:
            progress.completed = False
            progress.skipped = True
        else:
            progress = Progress(
                habit_id=habit_id,
                completed=False,
                skipped=True
            )
            session.add(progress)

        session.commit()

        await update.message.reply_text(
            f"⏭ Привычка «{habit.name}» пропущена на сегодня.\n"
            "Не забудьте вернуться к ней завтра!"
        )
    finally:
        close_session()

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats для показа статистики"""
    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("Сначала используйте команду /start")
            return

        habits = session.query(Habit).filter_by(user_id=user.id).all()
        if not habits:
            await update.message.reply_text(
                "У вас пока нет привычек. Добавьте их командой /add_habit"
            )
            return

        # Создаем клавиатуру с привычками
        keyboard = []
        for habit in habits:
            keyboard.append([
                InlineKeyboardButton(
                    habit.name,
                    callback_data=f"stats_{habit.id}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Выберите привычку для просмотра статистики:",
            reply_markup=reply_markup
        )
    finally:
        close_session()

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback-запросов для статистики"""
    query = update.callback_query
    await query.answer()

    habit_id = int(query.data.split('_')[1])
    session = get_session()
    try:
        habit = session.query(Habit).get(habit_id)
        if not habit:
            await query.message.reply_text("Привычка не найдена")
            return

        # Генерируем графики и отчет
        weekly_progress = generate_weekly_progress(habit_id)
        completion_rate = generate_completion_rate(habit_id)
        weekly_report = get_weekly_report(habit_id)

        # Отправляем отчет
        await query.message.reply_text(weekly_report)

        # Отправляем графики
        if weekly_progress:
            await query.message.reply_photo(
                photo=open(weekly_progress, 'rb'),
                caption="Прогресс за неделю"
            )

        if completion_rate:
            await query.message.reply_photo(
                photo=open(completion_rate, 'rb'),
                caption="Общая статистика выполнения"
            )
    finally:
        close_session()

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /reminder для настройки напоминаний"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "Использование: /reminder <id_привычки> <время1> [время2] ...\n"
            "Пример: /reminder 1 09:00 21:00"
        )
        return

    habit_id = int(context.args[0])
    times = context.args[1:]

    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("Сначала используйте команду /start")
            return

        habit = session.query(Habit).filter_by(id=habit_id, user_id=user.id).first()
        if not habit:
            await update.message.reply_text("Привычка не найдена")
            return

        # Обновляем время напоминаний
        habit.reminder_times = json.dumps(times)
        session.commit()

        # Обновляем напоминания в планировщике
        context.bot_data['reminder_manager'].update_reminder(habit_id, times)

        await update.message.reply_text(
            f"⏰ Напоминания для привычки «{habit.name}» обновлены!\n"
            f"Время: {', '.join(times)}"
        )
    finally:
        close_session() 