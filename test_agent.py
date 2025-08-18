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

from agent.main_agent.main import agent_executor
from config import setup_development_logging, get_logger

# Set up colored logging
setup_development_logging()
logger = get_logger(__name__)

def test_agent():
    """Test the agent with a simple query"""
    try:
        # Test basic functionality
        logger.info("Testing LangChain agent...")
        
        # Test a simple question
        logger.debug("Sending test query to agent")
        response = agent_executor.invoke({"input": "Hello, what are you capable of?"})
        
        agent_output = response.get("output", "No output received")
        logger.info("Agent Response received successfully")
        print("Agent Response:", agent_output)
        
        print("\n" + "="*50)
        logger.info("Agent successfully tested with colored logging!")
        
    except Exception as e:
        logger.error(f"Error testing agent: {e}", exc_info=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent()
