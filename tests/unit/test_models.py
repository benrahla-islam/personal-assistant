"""
Unit tests for database models.
Tests the refactored SQLAlchemy models with proper relationships, enums, and constraints.
"""

import pytest
from datetime import datetime, date, time
from sqlalchemy import inspect

from database.models import (
    Tag, Habit, Task, DailySchedule, HabitScheduleItem, TaskScheduleItem,
    FrequencyType, TaskType, VolumeSize, DayType, TaskStatus
)


@pytest.mark.unit
class TestDatabaseModels:
    """Test database models functionality."""

    def test_tag_creation(self, test_session):
        """Test creating a tag."""
        tag = Tag(name="Health", color="#FF5733")
        test_session.add(tag)
        test_session.commit()
        
        assert tag.id is not None
        assert tag.name == "Health"
        assert tag.color == "#FF5733"
        assert tag.created_at is not None
        assert not tag.is_deleted

    def test_habit_creation_with_enums(self, test_session):
        """Test creating a habit with enum values and relationships."""
        # Create tag first with unique name
        tag = Tag(name="Health-Habit-Test", color="#FF5733")
        test_session.add(tag)
        test_session.flush()
        
        # Create habit
        habit = Habit(
            name="Morning Exercise",
            frequency_type=FrequencyType.DAILY,
            estimated_duration=30,
            priority_level=8
        )
        habit.tags.append(tag)
        test_session.add(habit)
        test_session.commit()
        
        assert habit.id is not None
        assert habit.name == "Morning Exercise"
        assert habit.frequency_type == FrequencyType.DAILY
        assert habit.estimated_duration == 30
        assert habit.priority_level == 8
        assert len(habit.tags) == 1
        assert habit.tags[0].name == "Health-Habit-Test"

    def test_task_creation_with_enums(self, test_session):
        """Test creating a task with proper enum values."""
        # Create tag first
        tag = Tag(name="Work", color="#0066CC")
        test_session.add(tag)
        test_session.flush()
        
        # Create task
        task = Task(
            title="Complete project proposal",
            description="Write the final proposal for the new project",
            task_type=TaskType.ONE_TIME,
            priority_level=9,
            volume_size=VolumeSize.LARGE,
            estimated_duration=120
        )
        task.tags.append(tag)
        test_session.add(task)
        test_session.commit()
        
        assert task.id is not None
        assert task.title == "Complete project proposal"
        assert task.task_type == TaskType.ONE_TIME
        assert task.volume_size == VolumeSize.LARGE
        assert task.status == TaskStatus.PENDING  # Default value
        assert len(task.tags) == 1

    def test_daily_schedule_creation(self, test_session):
        """Test creating a daily schedule."""
        schedule = DailySchedule(
            schedule_date=date.today(),
            day_type=DayType.WORK_DAY,
            total_available_time=480
        )
        test_session.add(schedule)
        test_session.commit()
        
        assert schedule.id is not None
        assert schedule.schedule_date == date.today()
        assert schedule.day_type == DayType.WORK_DAY
        assert schedule.total_available_time == 480

    def test_schedule_items_creation(self, test_session):
        """Test creating schedule items with proper foreign key relationships."""
        from datetime import datetime, timedelta
        unique_date = date.today() + timedelta(days=1)  # Use tomorrow to avoid conflicts
        
        # Create dependencies
        tag = Tag(name="Health-Schedule", color="#FF5733")
        habit = Habit(
            name="Morning Exercise Schedule",
            frequency_type=FrequencyType.DAILY,
            estimated_duration=30,
            priority_level=8
        )
        task = Task(
            title="Project work schedule",
            task_type=TaskType.ONE_TIME,
            priority_level=7
        )
        schedule = DailySchedule(
            schedule_date=unique_date,
            day_type=DayType.WORK_DAY,
            total_available_time=480
        )
        
        test_session.add_all([tag, habit, task, schedule])
        test_session.flush()  # Get IDs without committing
        
        # Create schedule items
        habit_item = HabitScheduleItem(
            schedule_id=schedule.id,
            habit_id=habit.id,
            suggested_time=time(7, 0),
            priority_score=8.5,
            estimated_duration=30
        )
        
        task_item = TaskScheduleItem(
            schedule_id=schedule.id,
            task_id=task.id,
            suggested_time=time(9, 0),
            priority_score=9.0,
            estimated_duration=120
        )
        
        test_session.add_all([habit_item, task_item])
        test_session.commit()
        
        assert habit_item.id is not None
        assert task_item.id is not None
        assert habit_item.habit_id == habit.id
        assert task_item.task_id == task.id

    def test_model_validation(self, test_session):
        """Test that model validation works correctly."""
        with pytest.raises(ValueError, match="Duration must be positive"):
            invalid_habit = Habit(
                name="Invalid habit",
                frequency_type=FrequencyType.DAILY,
                estimated_duration=-10  # Should fail validation
            )
            test_session.add(invalid_habit)
            test_session.commit()

    def test_soft_delete_functionality(self, test_session):
        """Test soft delete and QueryMixin functionality."""
        # Create a tag
        tag = Tag(name="Test Tag", color="#FF0000")
        test_session.add(tag)
        test_session.commit()
        
        original_count = test_session.query(Tag).count()
        
        # Soft delete
        tag.soft_delete()
        test_session.commit()
        
        # Check counts
        active_count = Tag.active_query(test_session).count()
        total_count = test_session.query(Tag).count()
        
        assert active_count == 0, "Soft delete failed - still appears in active query"
        assert total_count == original_count, "Hard delete occurred instead of soft delete"
        assert tag.is_deleted is True
        assert tag.deleted_at is not None

    def test_relationships(self, test_session):
        """Test that model relationships work correctly."""
        from datetime import timedelta
        unique_date = date.today() + timedelta(days=2)  # Use day after tomorrow
        
        # Create habit with schedule item
        habit = Habit(
            name="Test Habit Relationships",
            frequency_type=FrequencyType.DAILY,
            estimated_duration=30
        )
        schedule = DailySchedule(
            schedule_date=unique_date,
            day_type=DayType.WORK_DAY,
            total_available_time=480
        )
        
        test_session.add_all([habit, schedule])
        test_session.flush()
        
        habit_item = HabitScheduleItem(
            schedule_id=schedule.id,
            habit_id=habit.id,
            suggested_time=time(7, 0),
            priority_score=8.5,
            estimated_duration=30
        )
        test_session.add(habit_item)
        test_session.commit()
        
        # Test relationships
        habit_with_items = test_session.query(Habit).filter(Habit.id == habit.id).first()
        assert len(habit_with_items.schedule_items) == 1
        assert habit_with_items.schedule_items[0].schedule_id == schedule.id

    def test_database_indexes(self, test_database_engine):
        """Test that database indexes are properly created."""
        inspector = inspect(test_database_engine)
        
        # Check that indexes exist on important tables
        habit_indexes = inspector.get_indexes('habits')
        task_indexes = inspector.get_indexes('tasks')
        schedule_indexes = inspector.get_indexes('daily_schedules')
        
        assert len(habit_indexes) > 0, "No indexes found on habits table"
        assert len(task_indexes) > 0, "No indexes found on tasks table"
        assert len(schedule_indexes) > 0, "No indexes found on daily_schedules table"

    def test_audit_fields(self, test_session):
        """Test that audit fields are automatically populated."""
        import time
        
        habit = Habit(
            name="Test Habit Audit",
            frequency_type=FrequencyType.DAILY,
            estimated_duration=30
        )
        test_session.add(habit)
        test_session.commit()
        
        assert habit.created_at is not None
        assert habit.updated_at is not None
        assert habit.created_at == habit.updated_at  # Should be equal on creation
        
        # Test updated_at changes on modification
        original_updated_at = habit.updated_at
        time.sleep(1)  # Ensure time difference
        habit.name = "Updated Habit Name"
        test_session.commit()
        
        assert habit.updated_at > original_updated_at
