import pytest
from agent.memory_pruner import prune_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agent.tools.tool_registry import register_tool, register_tools

def test_prune_messages():
    # Mock LLM is not even needed if we have few messages or we mock it
    # But let's test the logic of keeping 'N' recent messages.
    messages = [
        HumanMessage(content="Hello"),
        AIMessage(content="Hi"),
        HumanMessage(content="How are you?"),
        AIMessage(content="I am fine"),
        HumanMessage(content="What is the weather?"),
    ]
    
    # Mock LLM for summarization
    class MockLLM:
        def invoke(self, msgs):
            return AIMessage(content="Summary of conversation")
            
    llm = MockLLM()
    
    # Threshold 2: Keep min(6, 2) = 2 recent, summarize rest
    pruned = prune_messages(messages, llm, threshold=2)
    
    assert len(pruned) == 3 # 1 System (summary) + 2 recent
    assert isinstance(pruned[0], SystemMessage)
    assert "Summary of conversation" in pruned[0].content
    assert pruned[-1].content == "What is the weather?"
    assert pruned[-2].content == "I am fine"

def test_tool_registry(monkeypatch):
    # Mocking real tool imports to avoid credential errors
    from agent.tools import tool_registry
    monkeypatch.setattr(tool_registry, "_TOOL_REGISTRY", {})
    
    @register_tool("test_category")
    def test_tool():
        """A test tool."""
        return "test"
        
    tools = register_tools("test_category")
    assert any(t.name == "test_tool" for t in tools)
