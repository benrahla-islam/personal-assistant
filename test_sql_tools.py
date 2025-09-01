"""
Test the SQL tools functionality.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent.tools.planner_tools.database_tools import sql_query_tool, list_tables_tool

def test_sql_tools():
    """Test SQL query functionality."""
    
    print("🔍 Testing SQL Tools")
    print("=" * 50)
    
    # Test 1: List tables
    print("\n1. Listing all tables...")
    result = list_tables_tool.invoke({})
    print(f"Result: {result}")
    
    # Test 2: Query users
    print("\n2. Querying users table...")
    result = sql_query_tool.invoke({
        "query": "SELECT * FROM users"
    })
    print(f"Result: {result}")
    
    # Test 3: Query habits
    print("\n3. Querying habits table...")
    result = sql_query_tool.invoke({
        "query": "SELECT * FROM habits"
    })
    print(f"Result: {result}")
    
    # Test 4: Query tasks
    print("\n4. Querying tasks table...")
    result = sql_query_tool.invoke({
        "query": "SELECT id, title, status, priority_base FROM tasks"
    })
    print(f"Result: {result}")
    
    # Test 5: Test security (should fail)
    print("\n5. Testing security (trying INSERT - should fail)...")
    result = sql_query_tool.invoke({
        "query": "INSERT INTO users (username, email) VALUES ('hacker', 'hack@example.com')"
    })
    print(f"Result: {result}")
    
    print("\n✅ SQL tools test completed!")

if __name__ == "__main__":
    test_sql_tools()
