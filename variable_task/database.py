from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models.models import Base
from config import DATABASE_URL

# Создание движка базы данных
engine = create_engine(DATABASE_URL)

# Создание фабрики сессий
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(engine)

def get_session():
    """Получение сессии базы данных"""
    return Session()

def close_session():
    """Закрытие сессии базы данных"""
    Session.remove()

# Инициализация базы данных при импорте
init_db() 