import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN
from database import get_session, close_session
from models.models import User, Habit, Progress, HabitType
from utils.reminders import ReminderManager
from handlers.commands import (
    done_habit, skip_habit, show_stats,
    stats_callback, set_reminder
)
import json

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        if not user:
            user = User(
                telegram_id=update.effective_user.id,
                username=update.effective_user.username
            )
            session.add(user)
            session.commit()
        
        await update.message.reply_text(
            "👋 Привет! Я бот для формирования полезных привычек.\n\n"
            "Доступные команды:\n"
            "/add_habit - Добавить новую привычку\n"
            "/list_habits - Список ваших привычек\n"
            "/done <id> - Отметить привычку как выполненную\n"
            "/skip <id> - Пропустить привычку\n"
            "/stats - Статистика выполнения\n"
            "/reminder <id> <время> - Настроить напоминания\n"
            "/help - Помощь по командам"
        )
    finally:
        close_session()

async def add_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /add_habit"""
    if not context.args:
        await update.message.reply_text(
            "Использование: /add_habit \"Название привычки\" [daily|times_per_day|weekly] [цель]"
        )
        return

    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("Сначала используйте команду /start")
            return

        name = context.args[0].strip('"')
        habit_type = context.args[1] if len(context.args) > 1 else "daily"
        target = int(context.args[2]) if len(context.args) > 2 else 1

        habit = Habit(
            user_id=user.id,
            name=name,
            type=HabitType(habit_type),
            target=target,
            reminder_times=json.dumps(["09:00", "21:00"])
        )
        session.add(habit)
        session.commit()

        # Добавляем напоминания в планировщик
        context.bot_data['reminder_manager'].update_reminder(
            habit.id,
            json.loads(habit.reminder_times)
        )

        await update.message.reply_text(
            f"✅ Привычка «{name}» успешно добавлена!\n"
            f"Тип: {habit_type}\n"
            f"Цель: {target} раз в {'день' if habit_type != 'weekly' else 'неделю'}\n\n"
            f"ID привычки: {habit.id}\n"
            "Используйте этот ID для отметки выполнения и настройки напоминаний"
        )
    finally:
        close_session()

async def list_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /list_habits"""
    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        if not user:
            await update.message.reply_text("Сначала используйте команду /start")
            return

        habits = session.query(Habit).filter_by(user_id=user.id).all()
        if not habits:
            await update.message.reply_text("У вас пока нет привычек. Добавьте их командой /add_habit")
            return

        message = "📋 Ваши привычки:\n\n"
        for habit in habits:
            message += f"• {habit.name} (ID: {habit.id})\n"
            message += f"  Тип: {habit.type.value}\n"
            message += f"  Цель: {habit.target} раз в {'день' if habit.type != HabitType.WEEKLY else 'неделю'}\n"
            message += f"  Напоминания: {', '.join(json.loads(habit.reminder_times))}\n\n"

        await update.message.reply_text(message)
    finally:
        close_session()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "🤖 Помощь по командам:\n\n"
        "/start - Начать работу с ботом\n"
        "/add_habit \"Название\" [тип] [цель] - Добавить привычку\n"
        "  Типы: daily, times_per_day, weekly\n"
        "  Пример: /add_habit \"Читать\" daily 1\n"
        "/list_habits - Показать список привычек\n"
        "/done <id> - Отметить привычку как выполненную\n"
        "/skip <id> - Пропустить привычку\n"
        "/stats - Показать статистику\n"
        "/reminder <id> <время> - Настроить напоминания\n"
        "  Пример: /reminder 1 09:00 21:00\n"
        "/help - Показать это сообщение"
    )
    await update.message.reply_text(help_text)

def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Инициализация менеджера напоминаний
    application.bot_data['reminder_manager'] = ReminderManager(application.bot)
    application.bot_data['reminder_manager'].setup_reminders()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_habit", add_habit))
    application.add_handler(CommandHandler("list_habits", list_habits))
    application.add_handler(CommandHandler("done", done_habit))
    application.add_handler(CommandHandler("skip", skip_habit))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(CommandHandler("reminder", set_reminder))
    application.add_handler(CommandHandler("help", help_command))

    # Регистрация обработчика callback-запросов
    application.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats_"))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main() 