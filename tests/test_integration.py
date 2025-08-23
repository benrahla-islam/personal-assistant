import pytest
from unittest.mock import patch, MagicMock
import asyncio
from datetime import datetime, timedelta
import os


class TestEndToEndWorkflow:
    """End-to-end integration tests for the complete system."""
    
    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    @patch('agent.tools.extra_tools.DuckDuckGoSearchRun')
    def test_search_and_respond_workflow(self, mock_search):
        """Test complete workflow: user asks question → agent searches → responds."""
        from agent.main import agent_executor
        
        # Mock search results
        mock_search_instance = MagicMock()
        mock_search.return_value = mock_search_instance
        mock_search_instance.run.return_value = "Python is a programming language created by Guido van Rossum."
        
        # Simulate user asking about Python
        response = agent_executor.invoke({
            "input": "What is Python programming language?"
        })
        
        assert isinstance(response, dict)
        assert "output" in response
        output = response["output"]
        
        # Should mention Python in some way
        assert ("python" in output.lower() or 
                "programming" in output.lower() or
                "language" in output.lower())

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_schedule_and_list_workflow(self):
        """Test workflow: schedule task → list tasks → verify task appears."""
        from agent.main import agent_executor
        
        # Clear any existing tasks first
        from agent.tools.task_scheduler import get_scheduler
        scheduler = get_scheduler()
        for job in scheduler.get_jobs():
            scheduler.remove_job(job.id)
        
        # Step 1: Schedule a task
        future_time = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        schedule_response = agent_executor.invoke({
            "input": f"Schedule a reminder to 'Call mom' at {future_time} for chat 123"
        })
        
        assert "scheduled" in schedule_response["output"].lower()
        
        # Step 2: List tasks to verify it was scheduled
        list_response = agent_executor.invoke({
            "input": "List my scheduled tasks"
        })
        
        assert ("scheduled tasks" in list_response["output"].lower() or
                "call mom" in list_response["output"].lower())

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_conversation_memory_workflow(self):
        """Test that conversation memory works across multiple interactions."""
        from agent.main import agent_executor
        
        # First interaction - provide information
        response1 = agent_executor.invoke({
            "input": "My favorite programming language is Python"
        })
        
        # Second interaction - ask about previously mentioned information
        response2 = agent_executor.invoke({
            "input": "What did I say my favorite programming language was?"
        })
        
        # Should remember Python from the previous conversation
        assert "python" in response2["output"].lower()

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    @patch('agent.tools.telegram_scraper.TelethonChannelCollector')
    def test_telegram_scraping_workflow(self, mock_collector_class):
        """Test workflow: user asks for news → agent scrapes Telegram → provides summary."""
        from agent.main import agent_executor
        
        # Mock telegram scraper
        mock_instance = MagicMock()
        mock_collector_class.return_value = mock_instance
        mock_instance.start_client.return_value = True
        mock_instance.get_recent_messages.return_value = [
            {"text": "Breaking: Important news update", "date": "2025-08-21", "views": 1000}
        ]
        
        # User asks for latest news
        response = agent_executor.invoke({
            "input": "Get me the latest news from Telegram channels"
        })
        
        assert isinstance(response, dict)
        assert "output" in response
        # Should either show news or indicate an attempt was made
        output = response["output"].lower()
        assert ("news" in output or 
                "telegram" in output or 
                "messages" in output or
                "channel" in output)

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_error_recovery_workflow(self):
        """Test that system recovers gracefully from errors."""
        from agent.main import agent_executor
        
        # Try to schedule a task with invalid date (should handle gracefully)
        response = agent_executor.invoke({
            "input": "Schedule a task for yesterday at 25:99:99"
        })
        
        assert isinstance(response, dict)
        assert "output" in response
        # Should handle error gracefully without crashing
        output = response["output"]
        assert isinstance(output, str)
        assert len(output) > 0
        # Should indicate there was an issue with the request
        assert ("error" in output.lower() or 
                "invalid" in output.lower() or
                "sorry" in output.lower() or
                "can't" in output.lower())

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_multi_tool_workflow(self):
        """Test workflow that might use multiple tools."""
        from agent.main import agent_executor
        
        # Ask for something that might require both search and scheduling
        response = agent_executor.invoke({
            "input": "Search for 'meeting best practices' and then remind me about it in 2 hours"
        })
        
        assert isinstance(response, dict)
        assert "output" in response
        output = response["output"]
        
        # Should attempt to handle the complex request
        assert len(output) > 0
        # Should mention either searching, scheduling, or both
        assert ("search" in output.lower() or 
                "remind" in output.lower() or
                "schedule" in output.lower() or
                "meeting" in output.lower())


class TestSystemResilience:
    """Test system resilience and error handling."""
    
    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_agent_with_invalid_tool_input(self):
        """Test agent handles invalid tool inputs gracefully."""
        from agent.main import agent_executor
        
        # This should not crash the system
        response = agent_executor.invoke({
            "input": "Schedule a task with completely invalid parameters"
        })
        
        assert isinstance(response, dict)
        assert "output" in response
        assert isinstance(response["output"], str)

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_agent_with_very_long_input(self):
        """Test agent handles very long inputs."""
        from agent.main import agent_executor
        
        # Create a very long input
        long_input = "Please help me with this task: " + "A" * 1000
        
        response = agent_executor.invoke({"input": long_input})
        
        assert isinstance(response, dict)
        assert "output" in response
        assert isinstance(response["output"], str)

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    def test_agent_with_empty_input(self):
        """Test agent handles empty or minimal input."""
        from agent.main import agent_executor
        
        response = agent_executor.invoke({"input": ""})
        
        assert isinstance(response, dict)
        assert "output" in response
        assert isinstance(response["output"], str)
