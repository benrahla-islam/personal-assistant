import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
from agent.main_agent.main import agent_executor, agent
from agent.main_agent.custom_parser import JSONCapableReActOutputParser
from agent.main_agent.tool_regestery import register_tools


class TestMainAgent:
    """Test the main agent functionality."""
    
    def test_agent_executor_initialization(self):
        """Test that the agent executor is properly initialized."""
        assert agent_executor is not None
        assert hasattr(agent_executor, 'agent')
        assert hasattr(agent_executor, 'tools')
        assert hasattr(agent_executor, 'memory')
        assert agent_executor.verbose is True
        assert agent_executor.handle_parsing_errors is True
        assert agent_executor.max_iterations == 5

    def test_agent_tools_loaded(self):
        """Test that all expected tools are loaded."""
        tools = agent_executor.tools
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
        response = agent_executor.invoke({
            "input": "Hello, what are you capable of?"
        })
        
        assert isinstance(response, dict)
        assert "output" in response
        assert isinstance(response["output"], str)
        assert len(response["output"]) > 0

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_agent_memory_functionality(self):
        """Test that conversation memory works."""
        # First interaction
        response1 = agent_executor.invoke({
            "input": "My name is TestUser"
        })
        
        # Second interaction referencing first
        response2 = agent_executor.invoke({
            "input": "What's my name?"
        })
        
        assert "TestUser" in response2["output"] or "test" in response2["output"].lower()


class TestCustomParser:
    """Test the custom JSON parser."""
    
    def setup_method(self):
        """Setup parser for each test."""
        self.parser = JSONCapableReActOutputParser()

    def test_parse_valid_json_action(self):
        """Test parsing valid JSON tool action."""
        text = '''Thought: I need to schedule a task
Action: schedule_task
Action Input: {"prompt": "Test task", "run_at": "2025-08-22 10:00:00", "chat_id": "123", "task_name": "Test"}
Observation:'''
        
        result = self.parser.parse(text)
        assert hasattr(result, 'tool')
        assert result.tool == 'schedule_task'
        assert isinstance(result.tool_input, dict)
        assert result.tool_input['prompt'] == 'Test task'

    def test_parse_final_answer(self):
        """Test parsing final answer."""
        text = '''Thought: I have the information needed
Final Answer: Task scheduled successfully!'''
        
        result = self.parser.parse(text)
        assert hasattr(result, 'return_values')
        assert 'Task scheduled successfully!' in result.return_values['output']

    def test_parse_malformed_json(self):
        """Test handling of malformed JSON."""
        text = '''Thought: I need to schedule a task
Action: schedule_task
Action Input: {malformed json
Observation:'''
        
        # Should not raise exception, should handle gracefully
        result = self.parser.parse(text)
        assert result is not None


class TestToolRegistry:
    """Test tool registry functionality."""
    
    def test_register_all_tools(self):
        """Test registering all tools."""
        tools = register_tools('all')
        assert len(tools) == 6
        
        tool_names = [tool.name for tool in tools]
        expected = ['get_latest_messages', 'schedule_task', 'list_scheduled_tasks', 
                   'cancel_scheduled_task', 'search_tool', 'wiki_search_tool']
        
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
        """Test registering with invalid category falls back to all."""
        tools = register_tools('invalid_category')
        assert len(tools) == 6  # Should fallback to all tools


class TestAgentIntegration:
    """Integration tests for the complete agent system."""
    
    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    @patch('agent.tools.extra_tools.DuckDuckGoSearchRun')
    def test_agent_with_search_tool(self, mock_search):
        """Test agent using search tool."""
        # Mock the search tool
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance
        mock_search_instance.run.return_value = "Search results about Python"
        
        response = agent_executor.invoke({
            "input": "Search for information about Python programming"
        })
        
        assert isinstance(response, dict)
        assert "output" in response
        # Should contain either search results or indication that search was attempted
        assert len(response["output"]) > 0

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_agent_error_handling(self):
        """Test agent handles errors gracefully."""
        # Test with malformed input that might cause issues
        response = agent_executor.invoke({
            "input": "Schedule a task for yesterday"  # Invalid request
        })
        
        assert isinstance(response, dict)
        assert "output" in response
        # Should handle error gracefully without crashing
        assert isinstance(response["output"], str)
