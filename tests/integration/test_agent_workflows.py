import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
from agent.main import agent_executor, agent
from agent.tools.tool_registry import register_tools


class TestMainAgent:
    """Test the main agent functionality."""
    
    def test_agent_executor_initialization(self):
        """Test that the agent executor is properly initialized."""
        assert agent_executor is not None
        # In a LangGraph agent, tools are often accessible via the 'agent' node or tools property depending on version
        assert hasattr(agent_executor, 'name') or hasattr(agent_executor, 'builder') or hasattr(agent_executor, 'nodes')
        assert hasattr(agent_executor, 'checkpointer')

    def test_agent_tools_loaded(self):
        """Test that all expected tools are loaded."""
        tools = register_tools('all')
        tool_names = [tool.name for tool in tools]
        
        expected_tools = [
            'get_latest_messages',
            'schedule_task', 
            'list_scheduled_tasks',
            'cancel_scheduled_task',
            'search_tool',
            'wiki_search_tool'
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_agent_simple_query(self):
        """Test agent with a simple query."""
        from langchain_core.messages import HumanMessage
        response = agent_executor.invoke({
            "messages": [HumanMessage(content="Hello, what are you capable of?")]
        }, config={"configurable": {"thread_id": "test_simple"}})
        
        assert isinstance(response, dict)
        assert "messages" in response
        assert len(response["messages"]) > 0

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_agent_memory_functionality(self):
        """Test that conversation memory works."""
        from langchain_core.messages import HumanMessage
        
        config = {"configurable": {"thread_id": "test_memory"}}
        
        # First interaction
        response1 = agent_executor.invoke({
            "messages": [HumanMessage(content="My name is TestUser")]
        }, config=config)
        
        # Second interaction referencing first
        response2 = agent_executor.invoke({
            "messages": [HumanMessage(content="What's my name?")]
        }, config=config)
        
        final_message = response2["messages"][-1].content
        assert "TestUser" in final_message or "test" in final_message.lower()


class TestToolRegistry:
    """Test tool registry functionality."""
    
    def test_register_all_tools(self):
        """Test registering all tools."""
        tools = register_tools('all')
        # 1 telegram + 3 scheduler + 2 search + 2 agents + 14 database = 22
        assert len(tools) == 22
        
        tool_names = [tool.name for tool in tools]
        expected = [
            'get_latest_messages', 'schedule_task', 'list_scheduled_tasks', 
            'cancel_scheduled_task', 'search_tool', 'wiki_search_tool'
        ]
        
        for expected_tool in expected:
            assert expected_tool in tool_names

    def test_register_telegram_tools(self):
        """Test registering only telegram tools."""
        tools = register_tools('telegram')
        assert len(tools) == 1
        assert tools[0].name == 'get_latest_messages'

    def test_register_scheduler_tools(self):
        """Test registering only scheduler tools."""
        tools = register_tools('scheduler')
        assert len(tools) == 3
        
        tool_names = [tool.name for tool in tools]
        expected = ['schedule_task', 'list_scheduled_tasks', 'cancel_scheduled_task']
        
        for expected_tool in expected:
            assert expected_tool in tool_names

    def test_register_invalid_category(self):
        """Test registering with invalid category falls back to all + todoist tools."""
        tools = register_tools('invalid_category')
        # Fallback includes all tools + todoist tools = 26
        assert len(tools) == 26


class TestAgentIntegration:
    """Integration tests for the complete agent system."""
    
    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    @patch('agent.tools.extra_tools.DuckDuckGoSearchRun')
    def test_agent_with_search_tool(self, mock_search):
        """Test agent using search tool."""
        from langchain_core.messages import HumanMessage
        # Mock the search tool
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance
        mock_search_instance.run.return_value = "Search results about Python"
        
        response = agent_executor.invoke({
            "messages": [HumanMessage(content="Search for information about Python programming")]
        }, config={"configurable": {"thread_id": "test_search"}})
        
        assert isinstance(response, dict)
        assert "messages" in response
        # Should contain either search results or indication that search was attempted
        assert len(response["messages"]) > 0

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_agent_error_handling(self):
        """Test agent handles errors gracefully."""
        from langchain_core.messages import HumanMessage
        # Test with malformed input that might cause issues
        response = agent_executor.invoke({
            "messages": [HumanMessage(content="Schedule a task for yesterday")]  # Invalid request
        }, config={"configurable": {"thread_id": "test_error"}})
        
        assert isinstance(response, dict)
        assert "messages" in response
        # Should handle error gracefully without crashing
        assert len(response["messages"]) > 0
