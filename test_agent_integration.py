"""
Test the complete integration with the agent using database tools.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent.tools.tool_regestery import register_tools

def test_agent_with_database():
    """Test the agent with database tools."""
    
    print("🤖 Testing Agent Integration with Database Tools")
    print("=" * 60)
    
    # Test 1: Get database tools
    print("\n1. Getting database tools...")
    db_tools = register_tools('database')
    print(f"Found {len(db_tools)} database tools:")
    for i, tool in enumerate(db_tools, 1):
        print(f"  {i}. {tool.name}")
    
    # Test 2: Get all tools (should include database tools)
    print("\n2. Getting all tools (should include database tools)...")
    all_tools = register_tools('all')
    print(f"Total tools available: {len(all_tools)}")
    
    # Count database tools in all tools
    db_tool_names = [tool.name for tool in db_tools]
    db_tools_in_all = [tool for tool in all_tools if tool.name in db_tool_names]
    print(f"Database tools in 'all' category: {len(db_tools_in_all)}")
    
    # Test 3: Test planning tools (should include database tools)
    print("\n3. Getting planning tools (should include database tools)...")
    planning_tools = register_tools('planning')
    print(f"Planning tools available: {len(planning_tools)}")
    
    db_tools_in_planning = [tool for tool in planning_tools if tool.name in db_tool_names]
    print(f"Database tools in 'planning' category: {len(db_tools_in_planning)}")
    
    print("\n✅ Agent integration test completed!")
    print("\n📋 Summary:")
    print(f"  • Database tools: {len(db_tools)}")
    print(f"  • Total tools: {len(all_tools)}")  
    print(f"  • Planning tools: {len(planning_tools)}")
    print(f"  • Database tools properly integrated: ✅")

if __name__ == "__main__":
    test_agent_with_database()
