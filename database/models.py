"""
SQLAlchemy models for the Personal Assistant application.

This module defines the database models for managing habits, tasks,
task chains, daily schedules, and schedule items for a single user.
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, Time,
    Numeric, ForeignKey, UniqueConstraint, CheckConstraint,
    create_engine, MetaData, Index, Table, Enum
)
from sqlalchemy.orm import relationship, sessionmaker, Session, validates, declarative_base
from sqlalchemy.sql import func
import os

Base = declarative_base()


# Enums for better data integrity
class FrequencyType(PyEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    INTERVAL = "interval"


class TaskStatus(PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskType(PyEnum):
    ONE_TIME = "one_time"
    CHAIN_TASK = "chain_task"


class VolumeSize(PyEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class DayType(PyEnum):
    SCHOOL_DAY = "school_day"
    WORK_DAY = "work_day"
    FREE_DAY = "free_day"
    WEEKEND = "weekend"


class ScheduleStatus(PyEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    SKIPPED = "skipped"


# Association tables for many-to-many relationships
habit_tags = Table('habit_tags', Base.metadata,
    Column('habit_id', Integer, ForeignKey('habits.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

task_tags = Table('task_tags', Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


class Tag(Base):
    """Tag model for categorizing habits and tasks."""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(7))  # Hex color code like #FF5733
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    __table_args__ = (
        Index('idx_tag_name', 'name'),
        Index('idx_tag_active', 'is_deleted'),
    )


class Habit(Base):
    """Habit tracking model."""
    __tablename__ = 'habits'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    frequency_type = Column(Enum(FrequencyType), nullable=False)
    frequency_value = Column(Integer)  # days between sessions for interval type
    estimated_duration = Column(Integer, CheckConstraint('estimated_duration > 0'))  # minutes
    priority_level = Column(Integer, CheckConstraint('priority_level BETWEEN 1 AND 10'), nullable=False, default=5)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    completions = relationship("HabitCompletion", back_populates="habit", cascade="all, delete-orphan")
    schedule_items = relationship("HabitScheduleItem", back_populates="habit", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=habit_tags, backref="habits")
    time_entries = relationship("TimeEntry", back_populates="habit", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_habit_active', 'is_active'),
        Index('idx_habit_frequency', 'frequency_type'),
        Index('idx_habit_priority', 'priority_level'),
        Index('idx_habit_created', 'created_at'),
    )
    
    @validates('frequency_value')
    def validate_frequency_value(self, key, value):
        if self.frequency_type == FrequencyType.INTERVAL and (value is None or value <= 0):
            raise ValueError("Interval frequency requires positive value")
        return value
    
    @validates('estimated_duration')
    def validate_duration(self, key, duration):
        if duration is not None and duration <= 0:
            raise ValueError("Duration must be positive")
        return duration


class HabitCompletion(Base):
    """Habit completion tracking model."""
    __tablename__ = 'habit_completions'
    
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey('habits.id'), nullable=False)
    completed_at = Column(DateTime, default=func.now(), nullable=False)
    notes = Column(Text)
    actual_duration = Column(Integer)  # minutes actually spent
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    habit = relationship("Habit", back_populates="completions")
    
    __table_args__ = (
        Index('idx_completion_date', 'completed_at'),
        Index('idx_completion_habit', 'habit_id'),
        UniqueConstraint('habit_id', 'completed_at', name='unique_habit_completion_per_datetime'),
    )


class Task(Base):
    """Task management model."""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    task_type = Column(Enum(TaskType), nullable=False, default=TaskType.ONE_TIME)
    priority_level = Column(Integer, CheckConstraint('priority_level BETWEEN 1 AND 10'), nullable=False, default=5)
    due_date = Column(DateTime)
    estimated_duration = Column(Integer, CheckConstraint('estimated_duration > 0'))  # minutes
    volume_size = Column(Enum(VolumeSize))
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime)
    is_deleted = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)
    
    # Relationships
    chain_items = relationship("TaskChainItem", back_populates="task", cascade="all, delete-orphan")
    schedule_items = relationship("TaskScheduleItem", back_populates="task", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=task_tags, backref="tasks")
    time_entries = relationship("TimeEntry", back_populates="task", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="task", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_task_status', 'status'),
        Index('idx_task_due_date', 'due_date'),
        Index('idx_task_priority', 'priority_level'),
        Index('idx_task_created', 'created_at'),
        Index('idx_task_type', 'task_type'),
    )
    
    @validates('due_date')
    def validate_due_date(self, key, due_date):
        if due_date and due_date < datetime.now():
            raise ValueError("Due date cannot be in the past")
        return due_date
    
    @validates('estimated_duration')
    def validate_duration(self, key, duration):
        if duration is not None and duration <= 0:
            raise ValueError("Duration must be positive")
        return duration


class TaskChain(Base):
    """Task chain model for managing dependent tasks."""
    __tablename__ = 'task_chains'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    items = relationship("TaskChainItem", back_populates="chain", cascade="all, delete-orphan", order_by="TaskChainItem.sequence_order")
    
    __table_args__ = (
        Index('idx_chain_active', 'is_active'),
        Index('idx_chain_created', 'created_at'),
    )


class TaskChainItem(Base):
    """Task chain item model for ordering tasks within chains."""
    __tablename__ = 'task_chain_items'
    
    id = Column(Integer, primary_key=True)
    chain_id = Column(Integer, ForeignKey('task_chains.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Unique constraints
    __table_args__ = (
        UniqueConstraint('chain_id', 'task_id', name='unique_task_per_chain'),
        UniqueConstraint('chain_id', 'sequence_order', name='unique_sequence_per_chain'),
        Index('idx_chain_item_order', 'chain_id', 'sequence_order'),
    )
    
    # Relationships
    chain = relationship("TaskChain", back_populates="items")
    task = relationship("Task", back_populates="chain_items")


class DailySchedule(Base):
    """Daily schedule model for generated todo lists."""
    __tablename__ = 'daily_schedules'
    
    id = Column(Integer, primary_key=True)
    schedule_date = Column(Date, nullable=False, unique=True)
    day_type = Column(Enum(DayType), nullable=False)
    total_available_time = Column(Integer, CheckConstraint('total_available_time > 0'))  # minutes
    generated_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    habit_items = relationship("HabitScheduleItem", back_populates="schedule", cascade="all, delete-orphan")
    task_items = relationship("TaskScheduleItem", back_populates="schedule", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_schedule_date', 'schedule_date'),
        Index('idx_schedule_day_type', 'day_type'),
    )


class HabitScheduleItem(Base):
    """Schedule item model for habits in daily schedule."""
    __tablename__ = 'habit_schedule_items'
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('daily_schedules.id'), nullable=False)
    habit_id = Column(Integer, ForeignKey('habits.id'), nullable=False)
    suggested_time = Column(Time)
    priority_score = Column(Numeric(5, 2), CheckConstraint('priority_score >= 0'))
    estimated_duration = Column(Integer, CheckConstraint('estimated_duration > 0'))
    status = Column(Enum(ScheduleStatus), default=ScheduleStatus.SCHEDULED, nullable=False)
    completed_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    schedule = relationship("DailySchedule", back_populates="habit_items")
    habit = relationship("Habit", back_populates="schedule_items")
    
    __table_args__ = (
        Index('idx_habit_schedule_date_habit', 'schedule_id', 'habit_id'),
        Index('idx_habit_schedule_status', 'status'),
        Index('idx_habit_schedule_time', 'suggested_time'),
        UniqueConstraint('schedule_id', 'habit_id', name='unique_habit_per_schedule'),
    )


class TaskScheduleItem(Base):
    """Schedule item model for tasks in daily schedule."""
    __tablename__ = 'task_schedule_items'
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey('daily_schedules.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    suggested_time = Column(Time)
    priority_score = Column(Numeric(5, 2), CheckConstraint('priority_score >= 0'))
    estimated_duration = Column(Integer, CheckConstraint('estimated_duration > 0'))
    status = Column(Enum(ScheduleStatus), default=ScheduleStatus.SCHEDULED, nullable=False)
    completed_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    schedule = relationship("DailySchedule", back_populates="task_items")
    task = relationship("Task", back_populates="schedule_items")
    
    __table_args__ = (
        Index('idx_task_schedule_date_task', 'schedule_id', 'task_id'),
        Index('idx_task_schedule_status', 'status'),
        Index('idx_task_schedule_time', 'suggested_time'),
        UniqueConstraint('schedule_id', 'task_id', name='unique_task_per_schedule'),
    )


class TimeEntry(Base):
    """Time tracking model for habits and tasks."""
    __tablename__ = 'time_entries'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)
    habit_id = Column(Integer, ForeignKey('habits.id'), nullable=True)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime)
    duration_minutes = Column(Integer, CheckConstraint('duration_minutes > 0'))
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    task = relationship("Task", back_populates="time_entries")
    habit = relationship("Habit", back_populates="time_entries")
    
    __table_args__ = (
        Index('idx_time_entry_started', 'started_at'),
        Index('idx_time_entry_task', 'task_id'),
        Index('idx_time_entry_habit', 'habit_id'),
        CheckConstraint('(task_id IS NOT NULL AND habit_id IS NULL) OR (task_id IS NULL AND habit_id IS NOT NULL)', 
                       name='time_entry_single_reference'),
    )


class Reminder(Base):
    """Reminder model for tasks and habits."""
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)
    habit_id = Column(Integer, ForeignKey('habits.id'), nullable=True)
    remind_at = Column(DateTime, nullable=False)
    message = Column(String(500))
    is_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    sent_at = Column(DateTime)
    
    # Relationships
    task = relationship("Task", back_populates="reminders")
    habit = relationship("Habit")
    
    __table_args__ = (
        Index('idx_reminder_time', 'remind_at'),
        Index('idx_reminder_sent', 'is_sent'),
        Index('idx_reminder_task', 'task_id'),
        Index('idx_reminder_habit', 'habit_id'),
        CheckConstraint('(task_id IS NOT NULL AND habit_id IS NULL) OR (task_id IS NULL AND habit_id IS NOT NULL)', 
                       name='reminder_single_reference'),
    )


# Database utility functions
def create_database_engine(database_url: str = None):
    """Create and return a SQLAlchemy engine."""
    if database_url is None:
        database_url = os.getenv('DATABASE_URL', 'sqlite:///personal_assistant.db')
    return create_engine(database_url, echo=False)


def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)


def get_session_factory(engine):
    """Create and return a session factory."""
    return sessionmaker(bind=engine)


def get_session(session_factory) -> Session:
    """Get a database session."""
    return session_factory()


# Utility methods for common queries
class QueryMixin:
    """Mixin class for common query methods."""
    
    @classmethod
    def active_query(cls, session):
        """Get query for non-deleted items."""
        if hasattr(cls, 'is_deleted'):
            return session.query(cls).filter(cls.is_deleted == False)
        return session.query(cls)
    
    @classmethod
    def get_active_by_id(cls, session, item_id):
        """Get active item by ID."""
        return cls.active_query(session).filter(cls.id == item_id).first()
    
    def soft_delete(self):
        """Mark item as deleted."""
        if hasattr(self, 'is_deleted'):
            self.is_deleted = True
            if hasattr(self, 'updated_at'):
                self.updated_at = func.now()


# Add mixin to models
for model_class in [Habit, Task, TaskChain, DailySchedule, Tag]:
    model_class.__bases__ = model_class.__bases__ + (QueryMixin,)


# Example usage and database initialization
if __name__ == "__main__":
    # Create engine and tables
    engine = create_database_engine()
    create_tables(engine)
    
    # Create session factory
    SessionFactory = get_session_factory(engine)
    
    print("Database tables created successfully!")
    print("\nAvailable models:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
    
    print("\nEnum values:")
    print(f"FrequencyType: {[e.value for e in FrequencyType]}")
    print(f"TaskStatus: {[e.value for e in TaskStatus]}")
    print(f"VolumeSize: {[e.value for e in VolumeSize]}")
    print(f"DayType: {[e.value for e in DayType]}")
    print(f"ScheduleStatus: {[e.value for e in ScheduleStatus]}")
