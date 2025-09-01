"""
Test the database tools functionality.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent.tools.planner_tools.database_tools import (
    create_user_tool,
    get_user_tool,
    create_habit_tool,
    get_user_habits_tool,
    create_task_tool,
    get_user_tasks_tool,
    get_database_tools
)

def test_database_tools():
    """Test basic database operations."""
    
    print("🧪 Testing Database Tools")
    print("=" * 50)
    
    # Test 1: Create a user
    print("\n1. Creating a test user...")
    result = create_user_tool.invoke({
        "name": "Test User",
        "email": "test@example.com"
    })
    print(f"Result: {result}")
    
    # Test 2: Get the user
    print("\n2. Getting the user...")
    result = get_user_tool.invoke({
        "email": "test@example.com"
    })
    print(f"Result: {result}")
    
    # Test 3: Create a habit
    print("\n3. Creating a habit...")
    result = create_habit_tool.invoke({
        "user_id": 1,
        "name": "Morning Exercise",
        "frequency_type": "daily",
        "importance_level": 8
    })
    print(f"Result: {result}")
    
    # Test 4: Get user habits
    print("\n4. Getting user habits...")
    result = get_user_habits_tool.invoke({
        "user_id": 1
    })
    print(f"Result: {result}")
    
    # Test 5: Create a task
    print("\n5. Creating a task...")
    result = create_task_tool.invoke({
        "user_id": 1,
        "title": "Test Task",
        "description": "This is a test task",
        "due_date": "2025-01-16",
        "priority": "high"
    })
    print(f"Result: {result}")
    
    # Test 6: Get user tasks
    print("\n6. Getting user tasks...")
    result = get_user_tasks_tool.invoke({
        "user_id": 1
    })
    print(f"Result: {result}")
    
    # Test 7: Check tool count
    print("\n7. Checking tool count...")
    tools = get_database_tools()
    print(f"Total database tools available: {len(tools)}")
    
    for i, tool in enumerate(tools, 1):
        print(f"  {i}. {tool.name}")
    
    print("\n✅ Database tools test completed!")

if __name__ == "__main__":
    test_database_tools()
