"""
Database tools for the personal assistant agent.
Provides agent-friendly tools for managing single-user productivity data.
"""

from langchain_core.tools import tool
from sqlalchemy.orm import Session
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any
import json
import os

# Import the refactored models
from database.models import (
    Base, create_database_engine, create_tables, get_session_factory, get_session,
    Habit, HabitCompletion, Task, TaskChain, TaskChainItem, DailySchedule,
    HabitScheduleItem, TaskScheduleItem, Tag, TimeEntry, Reminder,
    FrequencyType, TaskStatus, TaskType, VolumeSize, DayType, ScheduleStatus
)
from config import get_logger

logger = get_logger(__name__)


"""
Database tools for the personal assistant agent.
Provides agent-friendly tools for managing single-user productivity data.
"""

from langchain_core.tools import tool
from sqlalchemy.orm import Session
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any
import json
import os

# Import the refactored models
from database.models import (
    Base, create_database_engine, create_tables, get_session_factory, get_session,
    Habit, HabitCompletion, Task, TaskChain, TaskChainItem, DailySchedule,
    HabitScheduleItem, TaskScheduleItem, Tag, TimeEntry, Reminder,
    FrequencyType, TaskStatus, TaskType, VolumeSize, DayType, ScheduleStatus
)
from config import get_logger

logger = get_logger(__name__)

# Database session management
_engine = None
_SessionFactory = None

def get_db_session():
    """Get a database session."""
    global _engine, _SessionFactory
    if _engine is None:
        _engine = create_database_engine()
        create_tables(_engine)
        _SessionFactory = get_session_factory(_engine)
    return _SessionFactory()


# Helper functions for data serialization
def habit_to_dict(habit: Habit) -> dict:
    """Convert habit to dictionary."""
    return {
        "id": habit.id,
        "name": habit.name,
        "frequency_type": habit.frequency_type.value,
        "frequency_value": habit.frequency_value,
        "estimated_duration": habit.estimated_duration,
        "priority_level": habit.priority_level,
        "is_active": habit.is_active,
        "created_at": habit.created_at.isoformat() if habit.created_at else None,
        "tags": [tag.name for tag in habit.tags] if habit.tags else []
    }

def task_to_dict(task: Task) -> dict:
    """Convert task to dictionary."""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type.value,
        "priority_level": task.priority_level,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "estimated_duration": task.estimated_duration,
        "volume_size": task.volume_size.value if task.volume_size else None,
        "status": task.status.value,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "tags": [tag.name for tag in task.tags] if task.tags else []
    }


# Habit Management Tools
@tool
def create_habit_tool(name: str, frequency_type: str, frequency_value: Optional[int] = None, 
                     estimated_duration: Optional[int] = None, priority_level: int = 5) -> str:
    """Create a new habit for daily tracking.
    
    Args:
        name: Habit name (e.g., "Morning Exercise", "Read for 30 minutes")
        frequency_type: How often ('daily', 'weekly', 'interval')
        frequency_value: Days between sessions (required for 'interval' type)
        estimated_duration: Expected duration in minutes
        priority_level: Importance level 1-10 (default: 5)
    
    Returns:
        Success message with habit ID
    """
    try:
        session = get_db_session()
        try:
            # Convert string to enum
            freq_enum = FrequencyType(frequency_type.lower())
            
            habit = Habit(
                name=name,
                frequency_type=freq_enum,
                frequency_value=frequency_value,
                estimated_duration=estimated_duration,
                priority_level=priority_level
            )
            session.add(habit)
            session.commit()
            
            logger.info(f"Created habit: {name} (ID: {habit.id})")
            return f"Habit '{name}' created successfully with ID: {habit.id}"
            
        finally:
            session.close()
    except ValueError as e:
        return f"Invalid frequency_type. Use: daily, weekly, or interval. Error: {e}"
    except Exception as e:
        logger.error(f"Error creating habit: {e}")
        return f"Error creating habit: {str(e)}"


@tool
def get_habits_tool(active_only: bool = True) -> str:
    """Get all habits for daily planning.
    
    Args:
        active_only: Only return active habits (default: True)
    
    Returns:
        List of habits as JSON string
    """
    try:
        session = get_db_session()
        try:
            query = session.query(Habit)
            if active_only:
                query = query.filter(Habit.is_active == True, Habit.is_deleted == False)
            
            habits = query.all()
            habits_data = [habit_to_dict(habit) for habit in habits]
            
            return json.dumps(habits_data, indent=2)
            
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error getting habits: {e}")
        return f"Error getting habits: {str(e)}"


@tool
def complete_habit_tool(habit_id: int, actual_duration: Optional[int] = None, notes: Optional[str] = None) -> str:
    """Mark a habit as completed for today.
    
    Args:
        habit_id: ID of the habit to complete
        actual_duration: How long it actually took in minutes (optional)
        notes: Any notes about the completion (optional)
    
    Returns:
        Success message
    """
    try:
        session = get_db_session()
        try:
            habit = session.query(Habit).filter(Habit.id == habit_id).first()
            if not habit:
                return f"Habit with ID {habit_id} not found"
            
            completion = HabitCompletion(
                habit_id=habit_id,
                actual_duration=actual_duration,
                notes=notes
            )
            session.add(completion)
            session.commit()
            
            logger.info(f"Completed habit: {habit.name}")
            return f"Habit '{habit.name}' marked as completed"
            
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error completing habit: {e}")
        return f"Error completing habit: {str(e)}"


# Task Management Tools
@tool
def create_task_tool(title: str, description: str = "", due_date: Optional[str] = None, 
                    priority_level: int = 5, volume_size: str = "medium") -> str:
    """Create a new task.
    
    Args:
        title: Task title
        description: Task description (optional)
        due_date: Due date in YYYY-MM-DD format (optional)
        priority_level: Priority level 1-10 (default: 5)
        volume_size: Task size ('small', 'medium', 'large')
    
    Returns:
        Success message with task ID
    """
    try:
        session = get_db_session()
        try:
            due_date_obj = None
            if due_date:
                due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
            
            volume_enum = VolumeSize(volume_size.lower())
            
            task = Task(
                title=title,
                description=description,
                due_date=due_date_obj,
                priority_level=priority_level,
                volume_size=volume_enum
            )
            session.add(task)
            session.commit()
            
            logger.info(f"Created task: {title} (ID: {task.id})")
            return f"Task '{title}' created successfully with ID: {task.id}"
            
        finally:
            session.close()
    except ValueError as e:
        return f"Invalid volume_size. Use: small, medium, or large. Error: {e}"
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return f"Error creating task: {str(e)}"


@tool
def get_tasks_tool(status: Optional[str] = None, include_completed: bool = False) -> str:
    """Get tasks for planning and tracking.
    
    Args:
        status: Filter by status ('pending', 'in_progress', 'completed', 'cancelled')
        include_completed: Include completed tasks (default: False)
    
    Returns:
        List of tasks as JSON string
    """
    try:
        session = get_db_session()
        try:
            query = session.query(Task).filter(Task.is_deleted == False)
            
            if status:
                status_enum = TaskStatus(status.lower())
                query = query.filter(Task.status == status_enum)
            elif not include_completed:
                query = query.filter(Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]))
            
            tasks = query.order_by(Task.due_date.asc(), Task.priority_level.desc()).all()
            tasks_data = [task_to_dict(task) for task in tasks]
            
            return json.dumps(tasks_data, indent=2)
            
        finally:
            session.close()
    except ValueError as e:
        return f"Invalid status. Use: pending, in_progress, completed, or cancelled. Error: {e}"
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        return f"Error getting tasks: {str(e)}"


@tool
def complete_task_tool(task_id: int, notes: Optional[str] = None) -> str:
    """Mark a task as completed.
    
    Args:
        task_id: ID of the task to complete
        notes: Optional completion notes
    
    Returns:
        Success message
    """
    try:
        session = get_db_session()
        try:
            task = session.query(Task).filter(Task.id == task_id).first()
            if not task:
                return f"Task with ID {task_id} not found"
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            if notes:
                task.notes = notes
            
            session.commit()
            
            logger.info(f"Completed task: {task.title}")
            return f"Task '{task.title}' marked as completed"
            
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return f"Error completing task: {str(e)}"


# Schedule Management Tools
@tool
def create_daily_schedule_tool(schedule_date: str, day_type: str = "work_day", 
                              total_available_time: Optional[int] = None) -> str:
    """Create a daily schedule for a specific date.
    
    Args:
        schedule_date: Date in YYYY-MM-DD format
        day_type: Type of day ('work_day', 'school_day', 'free_day', 'weekend')
        total_available_time: Available time in minutes (optional)
    
    Returns:
        Success message with schedule ID
    """
    try:
        session = get_db_session()
        try:
            schedule_date_obj = datetime.strptime(schedule_date, "%Y-%m-%d").date()
            day_type_enum = DayType(day_type.lower())
            
            # Check if schedule already exists
            existing = session.query(DailySchedule).filter(
                DailySchedule.schedule_date == schedule_date_obj
            ).first()
            
            if existing:
                return f"Schedule already exists for {schedule_date} with ID: {existing.id}"
            
            schedule = DailySchedule(
                schedule_date=schedule_date_obj,
                day_type=day_type_enum,
                total_available_time=total_available_time
            )
            session.add(schedule)
            session.commit()
            
            logger.info(f"Created daily schedule for {schedule_date}")
            return f"Daily schedule created for {schedule_date} with ID: {schedule.id}"
            
        finally:
            session.close()
    except ValueError as e:
        return f"Invalid day_type. Use: work_day, school_day, free_day, or weekend. Error: {e}"
    except Exception as e:
        logger.error(f"Error creating daily schedule: {e}")
        return f"Error creating daily schedule: {str(e)}"


@tool
def get_daily_schedule_tool(schedule_date: str) -> str:
    """Get daily schedule for a specific date.
    
    Args:
        schedule_date: Date in YYYY-MM-DD format
    
    Returns:
        Daily schedule with items as JSON string
    """
    try:
        session = get_db_session()
        try:
            schedule_date_obj = datetime.strptime(schedule_date, "%Y-%m-%d").date()
            
            schedule = session.query(DailySchedule).filter(
                DailySchedule.schedule_date == schedule_date_obj
            ).first()
            
            if not schedule:
                return f"No schedule found for {schedule_date}"
            
            # Get habit items
            habit_items = []
            for item in schedule.habit_items:
                habit_items.append({
                    "id": item.id,
                    "type": "habit",
                    "habit_id": item.habit_id,
                    "habit_name": item.habit.name,
                    "suggested_time": item.suggested_time.strftime("%H:%M") if item.suggested_time else None,
                    "priority_score": float(item.priority_score) if item.priority_score else None,
                    "estimated_duration": item.estimated_duration,
                    "status": item.status.value
                })
            
            # Get task items
            task_items = []
            for item in schedule.task_items:
                task_items.append({
                    "id": item.id,
                    "type": "task",
                    "task_id": item.task_id,
                    "task_title": item.task.title,
                    "suggested_time": item.suggested_time.strftime("%H:%M") if item.suggested_time else None,
                    "priority_score": float(item.priority_score) if item.priority_score else None,
                    "estimated_duration": item.estimated_duration,
                    "status": item.status.value
                })
            
            schedule_data = {
                "id": schedule.id,
                "schedule_date": schedule.schedule_date.isoformat(),
                "day_type": schedule.day_type.value,
                "total_available_time": schedule.total_available_time,
                "habit_items": habit_items,
                "task_items": task_items,
                "generated_at": schedule.generated_at.isoformat() if schedule.generated_at else None
            }
            
            return json.dumps(schedule_data, indent=2)
            
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error getting daily schedule: {e}")
        return f"Error getting daily schedule: {str(e)}"


@tool
def add_habit_to_schedule_tool(schedule_date: str, habit_id: int, suggested_time: Optional[str] = None) -> str:
    """Add a habit to a daily schedule.
    
    Args:
        schedule_date: Date in YYYY-MM-DD format
        habit_id: ID of the habit to add
        suggested_time: Suggested time in HH:MM format (optional)
    
    Returns:
        Success message
    """
    try:
        session = get_db_session()
        try:
            schedule_date_obj = datetime.strptime(schedule_date, "%Y-%m-%d").date()
            
            schedule = session.query(DailySchedule).filter(
                DailySchedule.schedule_date == schedule_date_obj
            ).first()
            
            if not schedule:
                return f"No schedule found for {schedule_date}"
            
            habit = session.query(Habit).filter(Habit.id == habit_id).first()
            if not habit:
                return f"Habit with ID {habit_id} not found"
            
            # Check if already added
            existing = session.query(HabitScheduleItem).filter(
                HabitScheduleItem.schedule_id == schedule.id,
                HabitScheduleItem.habit_id == habit_id
            ).first()
            
            if existing:
                return f"Habit '{habit.name}' already in schedule for {schedule_date}"
            
            suggested_time_obj = None
            if suggested_time:
                suggested_time_obj = datetime.strptime(suggested_time, "%H:%M").time()
            
            habit_item = HabitScheduleItem(
                schedule_id=schedule.id,
                habit_id=habit_id,
                suggested_time=suggested_time_obj,
                estimated_duration=habit.estimated_duration,
                priority_score=float(habit.priority_level)
            )
            session.add(habit_item)
            session.commit()
            
            return f"Habit '{habit.name}' added to schedule for {schedule_date}"
            
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error adding habit to schedule: {e}")
        return f"Error adding habit to schedule: {str(e)}"


@tool
def add_task_to_schedule_tool(schedule_date: str, task_id: int, suggested_time: Optional[str] = None) -> str:
    """Add a task to a daily schedule.
    
    Args:
        schedule_date: Date in YYYY-MM-DD format
        task_id: ID of the task to add
        suggested_time: Suggested time in HH:MM format (optional)
    
    Returns:
        Success message
    """
    try:
        session = get_db_session()
        try:
            schedule_date_obj = datetime.strptime(schedule_date, "%Y-%m-%d").date()
            
            schedule = session.query(DailySchedule).filter(
                DailySchedule.schedule_date == schedule_date_obj
            ).first()
            
            if not schedule:
                return f"No schedule found for {schedule_date}"
            
            task = session.query(Task).filter(Task.id == task_id).first()
            if not task:
                return f"Task with ID {task_id} not found"
            
            # Check if already added
            existing = session.query(TaskScheduleItem).filter(
                TaskScheduleItem.schedule_id == schedule.id,
                TaskScheduleItem.task_id == task_id
            ).first()
            
            if existing:
                return f"Task '{task.title}' already in schedule for {schedule_date}"
            
            suggested_time_obj = None
            if suggested_time:
                suggested_time_obj = datetime.strptime(suggested_time, "%H:%M").time()
            
            task_item = TaskScheduleItem(
                schedule_id=schedule.id,
                task_id=task_id,
                suggested_time=suggested_time_obj,
                estimated_duration=task.estimated_duration,
                priority_score=float(task.priority_level)
            )
            session.add(task_item)
            session.commit()
            
            return f"Task '{task.title}' added to schedule for {schedule_date}"
            
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error adding task to schedule: {e}")
        return f"Error adding task to schedule: {str(e)}"


# Tag Management Tools
@tool
def create_tag_tool(name: str, color: Optional[str] = None) -> str:
    """Create a new tag for organizing habits and tasks.
    
    Args:
        name: Tag name (e.g., "Health", "Work", "Learning")
        color: Hex color code (e.g., "#FF5733", optional)
    
    Returns:
        Success message with tag ID
    """
    try:
        session = get_db_session()
        try:
            # Check if tag already exists
            existing = session.query(Tag).filter(Tag.name == name).first()
            if existing:
                return f"Tag '{name}' already exists with ID: {existing.id}"
            
            tag = Tag(name=name, color=color)
            session.add(tag)
            session.commit()
            
            return f"Tag '{name}' created successfully with ID: {tag.id}"
            
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error creating tag: {e}")
        return f"Error creating tag: {str(e)}"


@tool
def get_productivity_insights_tool(days: int = 7) -> str:
    """Get productivity insights and statistics.
    
    Args:
        days: Number of days to analyze (default: 7)
    
    Returns:
        Productivity insights as JSON string
    """
    try:
        session = get_db_session()
        try:
            from datetime import timedelta
            start_date = datetime.now().date() - timedelta(days=days)
            
            # Habit completions
            habit_completions = session.query(HabitCompletion).filter(
                HabitCompletion.completed_at >= start_date
            ).count()
            
            # Task completions
            completed_tasks = session.query(Task).filter(
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= start_date
            ).count()
            
            # Total tasks
            total_tasks = session.query(Task).filter(
                Task.created_at >= start_date,
                Task.is_deleted == False
            ).count()
            
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            insights = {
                "period_days": days,
                "habit_completions": habit_completions,
                "tasks_completed": completed_tasks,
                "total_tasks": total_tasks,
                "task_completion_rate": round(completion_rate, 1),
                "average_completions_per_day": round((habit_completions + completed_tasks) / days, 1)
            }
            
            return json.dumps(insights, indent=2)
            
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error getting productivity insights: {e}")
        return f"Error getting productivity insights: {str(e)}"


@tool
def search_items_tool(query: str, item_type: str = "both") -> str:
    """Search habits and tasks by name/title.
    
    Args:
        query: Search query
        item_type: Type to search ('habits', 'tasks', 'both')
    
    Returns:
        Search results as JSON string
    """
    try:
        session = get_db_session()
        try:
            results = {"habits": [], "tasks": []}
            
            if item_type in ["habits", "both"]:
                habits = session.query(Habit).filter(
                    Habit.name.ilike(f"%{query}%"),
                    Habit.is_deleted == False
                ).all()
                results["habits"] = [habit_to_dict(habit) for habit in habits]
            
            if item_type in ["tasks", "both"]:
                tasks = session.query(Task).filter(
                    Task.title.ilike(f"%{query}%"),
                    Task.is_deleted == False
                ).all()
                results["tasks"] = [task_to_dict(task) for task in tasks]
            
            return json.dumps(results, indent=2)
            
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error searching items: {e}")
        return f"Error searching items: {str(e)}"


def get_database_tools():
    """Get all database tools for the agent."""
    return [
        # Habit management
        create_habit_tool,
        get_habits_tool,
        complete_habit_tool,
        
        # Task management
        create_task_tool,
        get_tasks_tool,
        complete_task_tool,
        
        # Schedule management
        create_daily_schedule_tool,
        get_daily_schedule_tool,
        add_habit_to_schedule_tool,
        add_task_to_schedule_tool,
        
        # Organization
        create_tag_tool,
        
        # Analytics
        get_productivity_insights_tool,
        search_items_tool
    ]
