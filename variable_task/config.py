import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Токен бота
BOT_TOKEN = "8095041894:AAFr7z7gr0qVrwDTsF_RKBwA7gOPGdhVAgI"

# Настройки базы данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///habits.db')

# Настройки напоминаний
DEFAULT_REMINDER_TIMES = ['09:00', '21:00']
REMINDER_INTERVAL = 24  # часов

# Настройки для графиков
CHART_COLORS = ['#4CAF50', '#2196F3', '#FFC107', '#F44336', '#9C27B0']
CHART_STYLE = 'seaborn-v0_8'

# Пути к файлам
TEMP_DIR = 'temp'
STATS_DIR = 'stats'

# Создание необходимых директорий
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STATS_DIR, exist_ok=True) 