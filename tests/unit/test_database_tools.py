"""
Unit tests for database tools.
Tests the refactored LangChain database tools for the personal assistant agent.
"""

import pytest
import json
from datetime import date

from agent.tools.planner_tools.database_tools import get_database_tools


@pytest.mark.unit
class TestDatabaseTools:
    """Test database tools functionality."""

    @pytest.fixture(autouse=True)
    def setup_tools(self):
        """Set up database tools for each test."""
        self.tools = get_database_tools()
        self.tool_dict = {tool.name: tool for tool in self.tools}

    def test_tools_loaded(self):
        """Test that all expected database tools are loaded."""
        expected_tools = [
            "create_habit_tool",
            "get_habits_tool", 
            "complete_habit_tool",
            "create_task_tool",
            "get_tasks_tool",
            "complete_task_tool",
            "create_daily_schedule_tool",
            "get_daily_schedule_tool",
            "add_habit_to_schedule_tool",
            "add_task_to_schedule_tool",
            "create_tag_tool",
            "get_productivity_insights_tool",
            "search_items_tool"
        ]
        
        assert len(self.tools) == len(expected_tools)
        for tool_name in expected_tools:
            assert tool_name in self.tool_dict, f"Missing tool: {tool_name}"

    def test_create_and_get_habit(self):
        """Test creating and retrieving habits."""
        # Create habit
        create_result = self.tool_dict["create_habit_tool"].invoke({
            "name": "Morning Exercise",
            "frequency_type": "daily",
            "estimated_duration": 30,
            "priority_level": 8
        })
        
        assert "successfully" in create_result.lower()
        
        # Get habits
        get_result = self.tool_dict["get_habits_tool"].invoke({"active_only": True})
        habits = json.loads(get_result)
        
        assert len(habits) > 0
        assert any(h["name"] == "Morning Exercise" for h in habits)

    def test_complete_habit(self):
        """Test completing a habit."""
        # First create a habit
        self.tool_dict["create_habit_tool"].invoke({
            "name": "Reading",
            "frequency_type": "daily",
            "estimated_duration": 20,
            "priority_level": 7
        })
        
        # Get the habit ID
        habits_result = self.tool_dict["get_habits_tool"].invoke({"active_only": True})
        habits = json.loads(habits_result)
        habit_id = next(h["id"] for h in habits if h["name"] == "Reading")
        
        # Complete the habit
        complete_result = self.tool_dict["complete_habit_tool"].invoke({
            "habit_id": habit_id,
            "notes": "Felt great today!"
        })
        
        assert "completed" in complete_result.lower()

    def test_create_and_get_task(self):
        """Test creating and retrieving tasks."""
        # Create task
        create_result = self.tool_dict["create_task_tool"].invoke({
            "title": "Complete project proposal",
            "description": "Write the final proposal for the new project",
            "due_date": "2025-09-15",
            "priority_level": 9,
            "volume_size": "large"
        })
        
        assert "successfully" in create_result.lower()
        
        # Get tasks
        get_result = self.tool_dict["get_tasks_tool"].invoke({})
        tasks = json.loads(get_result)
        
        assert len(tasks) > 0
        assert any(t["title"] == "Complete project proposal" for t in tasks)

    def test_complete_task(self):
        """Test completing a task."""
        # First create a task
        self.tool_dict["create_task_tool"].invoke({
            "title": "Write report",
            "description": "Monthly status report",
            "priority_level": 6
        })
        
        # Get the task ID
        tasks_result = self.tool_dict["get_tasks_tool"].invoke({})
        tasks = json.loads(tasks_result)
        task_id = next(t["id"] for t in tasks if t["title"] == "Write report")
        
        # Complete the task
        complete_result = self.tool_dict["complete_task_tool"].invoke({
            "task_id": task_id,
            "notes": "Finished ahead of schedule"
        })
        
        assert "completed" in complete_result.lower()

    def test_daily_schedule_workflow(self):
        """Test complete daily schedule workflow."""
        test_date = "2025-09-15"
        
        # Create a schedule
        schedule_result = self.tool_dict["create_daily_schedule_tool"].invoke({
            "schedule_date": test_date,
            "day_type": "work_day",
            "total_available_time": 480
        })
        
        assert "successfully" in schedule_result.lower()
        
        # Create habit and task for the schedule
        self.tool_dict["create_habit_tool"].invoke({
            "name": "Meditation",
            "frequency_type": "daily",
            "estimated_duration": 15,
            "priority_level": 8
        })
        
        self.tool_dict["create_task_tool"].invoke({
            "title": "Review code",
            "description": "Code review session",
            "priority_level": 7
        })
        
        # Get IDs
        habits = json.loads(self.tool_dict["get_habits_tool"].invoke({"active_only": True}))
        tasks = json.loads(self.tool_dict["get_tasks_tool"].invoke({}))
        
        habit_id = next(h["id"] for h in habits if h["name"] == "Meditation")
        task_id = next(t["id"] for t in tasks if t["title"] == "Review code")
        
        # Add items to schedule
        habit_add_result = self.tool_dict["add_habit_to_schedule_tool"].invoke({
            "schedule_date": test_date,
            "habit_id": habit_id,
            "suggested_time": "07:00"
        })
        
        task_add_result = self.tool_dict["add_task_to_schedule_tool"].invoke({
            "schedule_date": test_date,
            "task_id": task_id,
            "suggested_time": "09:00"
        })
        
        assert "added" in habit_add_result.lower()
        assert "added" in task_add_result.lower()
        
        # Get the complete schedule
        schedule_result = self.tool_dict["get_daily_schedule_tool"].invoke({
            "schedule_date": test_date
        })
        
        schedule = json.loads(schedule_result)
        assert len(schedule["habit_items"]) > 0
        assert len(schedule["task_items"]) > 0

    def test_tag_creation(self):
        """Test creating tags."""
        result = self.tool_dict["create_tag_tool"].invoke({
            "name": "Health",
            "color": "#FF5733"
        })
        
        assert "successfully" in result.lower()

    def test_productivity_insights(self):
        """Test getting productivity insights."""
        # First complete some items to have data
        self.tool_dict["create_habit_tool"].invoke({
            "name": "Exercise",
            "frequency_type": "daily",
            "estimated_duration": 30
        })
        
        habits = json.loads(self.tool_dict["get_habits_tool"].invoke({"active_only": True}))
        habit_id = habits[0]["id"]
        
        self.tool_dict["complete_habit_tool"].invoke({
            "habit_id": habit_id,
            "notes": "Good workout"
        })
        
        # Get insights
        result = self.tool_dict["get_productivity_insights_tool"].invoke({"days": 7})
        insights = json.loads(result)
        
        assert "habit_completions" in insights
        assert "task_completions" in insights
        assert "completion_rate" in insights

    def test_search_functionality(self):
        """Test search functionality."""
        # Create items to search
        self.tool_dict["create_habit_tool"].invoke({
            "name": "Morning Yoga",
            "frequency_type": "daily",
            "estimated_duration": 20
        })
        
        self.tool_dict["create_task_tool"].invoke({
            "title": "Yoga class preparation",
            "description": "Prepare materials for yoga class"
        })
        
        # Search for yoga-related items
        result = self.tool_dict["search_items_tool"].invoke({
            "query": "Yoga",
            "item_type": "both"
        })
        
        search_results = json.loads(result)
        assert len(search_results["habits"]) > 0 or len(search_results["tasks"]) > 0

    def test_tool_error_handling(self):
        """Test that tools handle errors gracefully."""
        # Try to complete non-existent habit
        result = self.tool_dict["complete_habit_tool"].invoke({
            "habit_id": 99999,
            "notes": "This should fail"
        })
        
        assert "error" in result.lower() or "not found" in result.lower()

    def test_enum_validation(self):
        """Test that tools properly validate enum values."""
        # Try to create habit with invalid frequency type
        result = self.tool_dict["create_habit_tool"].invoke({
            "name": "Test Habit",
            "frequency_type": "invalid_frequency",
            "estimated_duration": 30
        })
        
        # Should handle the error gracefully
        assert isinstance(result, str)  # Tool should return a string response
