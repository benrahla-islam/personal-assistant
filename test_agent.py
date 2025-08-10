#!/usr/bin/env python3
"""
Test script for the LangChain agent
Run with: uv run test_agent.py
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.main import agent_executor

def test_agent():
    """Test the agent with a simple query"""
    try:
        # Test basic functionality
        print("Testing LangChain agent...")
        
        # Test a simple question
        response = agent_executor.invoke({"input": "Hello, what are you capable of?"})
        print("Agent Response:", response.get("output", "No output received"))
        
        print("\n" + "="*50)
        print("Agent successfully migrated to LangChain!")
        
    except Exception as e:
        print(f"Error testing agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent()
