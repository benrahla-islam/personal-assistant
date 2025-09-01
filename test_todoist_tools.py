#!/usr/bin/env python3
"""
Test script for Todoist tools
"""

import os
import asyncio
from agent.tools.planner_tools.todoist_tool import (
    todoist_add_tasks_tool,
    todoist_delete_task_tool,
    todoist_update_task_tool,
    todoist_get_tasks_by_date_tool
)

async def test_todoist_tools():
    """Test all Todoist tools"""
    
    # Check if API token is set
    if not os.getenv("TODOIST_API_TOKEN"):
        print("⚠️  TODOIST_API_TOKEN environment variable not set.")
        print("Please set your Todoist API token to test the tools:")
        print("export TODOIST_API_TOKEN='your_api_token_here'")
        print("\nYou can get your token from: https://todoist.com/prefs/integrations")
        return
    
    print("🧪 Testing Todoist tools...")
    
    # Test 1: Add tasks tool
    print("\n1. Testing todoist_add_tasks tool:")
    add_tool = todoist_add_tasks_tool()
    print(f"Tool name: {add_tool.name}")
    print(f"Description: {add_tool.description}")
    
    # Test 2: Delete task tool
    print("\n2. Testing todoist_delete_task tool:")
    delete_tool = todoist_delete_task_tool()
    print(f"Tool name: {delete_tool.name}")
    print(f"Description: {delete_tool.description}")
    
    # Test 3: Update task tool
    print("\n3. Testing todoist_update_task tool:")
    update_tool = todoist_update_task_tool()
    print(f"Tool name: {update_tool.name}")
    print(f"Description: {update_tool.description}")
    
    # Test 4: Get tasks by date tool
    print("\n4. Testing todoist_get_tasks_by_date tool:")
    get_tasks_tool = todoist_get_tasks_by_date_tool()
    print(f"Tool name: {get_tasks_tool.name}")
    print(f"Description: {get_tasks_tool.description}")
    
    print("\n✅ All tools created successfully!")
    
    # Test actual API calls (if token is available)
    try:
        print("\n🔄 Testing actual API calls...")
        
        # Test getting today's tasks
        result = await get_tasks_tool.func("today")
        print(f"Today's tasks result: {result}")
        
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        print("This might be because the API token is invalid or there's a network issue.")

if __name__ == "__main__":
    asyncio.run(test_todoist_tools())
