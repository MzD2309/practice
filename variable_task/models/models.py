from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class HabitType(enum.Enum):
    DAILY = "daily"
    TIMES_PER_DAY = "times_per_day"
    WEEKLY = "weekly"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    habits = relationship("Habit", back_populates="user")

class Habit(Base):
    __tablename__ = 'habits'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    type = Column(Enum(HabitType))
    target = Column(Integer)  # Количество раз в день/неделю
    created_at = Column(DateTime, default=datetime.utcnow)
    reminder_times = Column(String)  # JSON строка со временем напоминаний
    
    user = relationship("User", back_populates="habits")
    progress = relationship("Progress", back_populates="habit")

class Progress(Base):
    __tablename__ = 'progress'
    
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey('habits.id'))
    date = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)
    skipped = Column(Boolean, default=False)
    
    habit = relationship("Habit", back_populates="progress")

class Group(Base):
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    is_active = Column(Boolean, default=True)

class GroupMember(Base):
    __tablename__ = 'group_members'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    joined_at = Column(DateTime, default=datetime.utcnow) 