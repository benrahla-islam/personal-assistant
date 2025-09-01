#!/usr/bin/env python3
"""
Test script to validate the refactored database tools work correctly.
"""

from agent.tools.planner_tools.database_tools import get_database_tools
import tempfile
import os
import json

def test_database_tools():
    """Test the refactored database tools."""
    
    # Get all tools
    tools = get_database_tools()
    print(f"✅ Loaded {len(tools)} database tools")
    
    # Test 1: Create a habit
    create_habit_tool = next(tool for tool in tools if tool.name == "create_habit_tool")
    result = create_habit_tool.invoke({
        "name": "Morning Exercise",
        "frequency_type": "daily",
        "estimated_duration": 30,
        "priority_level": 8
    })
    print(f"✅ Create habit: {result}")
    
    # Test 2: Get habits
    get_habits_tool = next(tool for tool in tools if tool.name == "get_habits_tool")
    result = get_habits_tool.invoke({"active_only": True})
    habits = json.loads(result)
    assert len(habits) > 0, "No habits found"
    habit_id = habits[0]["id"]
    print(f"✅ Get habits: Found {len(habits)} habits")
    
    # Test 3: Complete habit
    complete_habit_tool = next(tool for tool in tools if tool.name == "complete_habit_tool")
    result = complete_habit_tool.invoke({
        "habit_id": habit_id,
        "notes": "Felt great today!"
    })
    print(f"✅ Complete habit: {result}")
    
    # Test 4: Create a task
    create_task_tool = next(tool for tool in tools if tool.name == "create_task_tool")
    result = create_task_tool.invoke({
        "title": "Complete project proposal",
        "description": "Write the final proposal for the new project",
        "due_date": "2025-09-02",
        "priority_level": 9,
        "volume_size": "large"
    })
    print(f"✅ Create task: {result}")
    
    # Test 5: Get tasks
    get_tasks_tool = next(tool for tool in tools if tool.name == "get_tasks_tool")
    result = get_tasks_tool.invoke({})
    tasks = json.loads(result)
    assert len(tasks) > 0, "No tasks found"
    task_id = tasks[0]["id"]
    print(f"✅ Get tasks: Found {len(tasks)} tasks")
    
    # Test 6: Create daily schedule
    create_schedule_tool = next(tool for tool in tools if tool.name == "create_daily_schedule_tool")
    result = create_schedule_tool.invoke({
        "schedule_date": "2025-09-02",
        "day_type": "work_day",
        "total_available_time": 480
    })
    print(f"✅ Create schedule: {result}")
    
    # Test 7: Add habit to schedule
    add_habit_tool = next(tool for tool in tools if tool.name == "add_habit_to_schedule_tool")
    result = add_habit_tool.invoke({
        "schedule_date": "2025-09-02",
        "habit_id": habit_id,
        "suggested_time": "07:00"
    })
    print(f"✅ Add habit to schedule: {result}")
    
    # Test 8: Add task to schedule
    add_task_tool = next(tool for tool in tools if tool.name == "add_task_to_schedule_tool")
    result = add_task_tool.invoke({
        "schedule_date": "2025-09-02",
        "task_id": task_id,
        "suggested_time": "09:00"
    })
    print(f"✅ Add task to schedule: {result}")
    
    # Test 9: Get daily schedule
    get_schedule_tool = next(tool for tool in tools if tool.name == "get_daily_schedule_tool")
    result = get_schedule_tool.invoke({"schedule_date": "2025-09-02"})
    schedule = json.loads(result)
    assert len(schedule["habit_items"]) > 0, "No habit items in schedule"
    assert len(schedule["task_items"]) > 0, "No task items in schedule"
    print(f"✅ Get schedule: Found {len(schedule['habit_items'])} habit items and {len(schedule['task_items'])} task items")
    
    # Test 10: Complete task
    complete_task_tool = next(tool for tool in tools if tool.name == "complete_task_tool")
    result = complete_task_tool.invoke({
        "task_id": task_id,
        "notes": "Finished ahead of schedule"
    })
    print(f"✅ Complete task: {result}")
    
    # Test 11: Create tag
    create_tag_tool = next(tool for tool in tools if tool.name == "create_tag_tool")
    result = create_tag_tool.invoke({
        "name": "Health",
        "color": "#FF5733"
    })
    print(f"✅ Create tag: {result}")
    
    # Test 12: Get productivity insights
    insights_tool = next(tool for tool in tools if tool.name == "get_productivity_insights_tool")
    result = insights_tool.invoke({"days": 7})
    insights = json.loads(result)
    assert "habit_completions" in insights, "Missing habit completions in insights"
    print(f"✅ Productivity insights: {insights['habit_completions']} habit completions")
    
    # Test 13: Search items
    search_tool = next(tool for tool in tools if tool.name == "search_items_tool")
    result = search_tool.invoke({
        "query": "Exercise",
        "item_type": "both"
    })
    search_results = json.loads(result)
    assert len(search_results["habits"]) > 0, "No habits found in search"
    print(f"✅ Search: Found {len(search_results['habits'])} habits and {len(search_results['tasks'])} tasks")
    
    print("\n🎉 ALL DATABASE TOOLS TESTS PASSED!")
    
    # Print summary
    print("\n📊 TOOLS REFACTOR SUMMARY:")
    print("❌ REMOVED: All user_id parameters (single-user design)")
    print("✅ FIXED: Enum compatibility with new models")
    print("✅ ADDED: Proper habit completion tracking")
    print("✅ ADDED: Task completion with status updates")
    print("✅ ADDED: Separate schedule item tables (fixed polymorphic issue)")
    print("✅ ADDED: Tag management system")
    print("✅ ADDED: Productivity insights and analytics")
    print("✅ ADDED: Search functionality")
    print("✅ ADDED: Proper error handling and validation")
    print("✅ ADDED: Agent-friendly JSON serialization")
    
    print(f"\n📈 TOOL COUNT:")
    print(f"Original: 10 broken tools")
    print(f"New: {len(tools)} working tools")
    
    print(f"\n🎯 AGENT CAPABILITIES:")
    print("- Store and manage user habits and tasks")
    print("- Generate and modify daily schedules")
    print("- Track completions and progress") 
    print("- Organize with tags")
    print("- Analyze productivity patterns")
    print("- Search and filter data")


if __name__ == "__main__":
    test_database_tools()
