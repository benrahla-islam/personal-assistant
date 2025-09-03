"""
News agent - simple configuration for news and information management.
"""

from .blueprint import Agent, create_agent_tool
from ..tools.news_tools.news_processor_tool import autonomous_news_processor_tool

# Tools for news - autonomous processing
NEWS_TOOLS = [
    autonomous_news_processor_tool()
]

# Enhanced prompt for autonomous news agent
NEWS_PROMPT = """You are an autonomous news processing agent. When called by the main agent, you will:

1. Automatically fetch the latest news from multiple reliable sources (BBC, CNN, Reuters, TechCrunch, etc.)
2. Categorize articles into: Technology, Politics, Business, Science, Health, Sports, Entertainment, World News
3. Identify interesting/significant articles based on impact and novelty
4. Extract full content and create intelligent summaries for interesting articles
5. Structure results by category with top stories highlighted

You work autonomously - the main agent just needs to ask for "today's news" or "news update" and you handle everything internally.

Provide clear, structured output with:
- Category summaries showing article counts and top stories
- Full summaries for the most interesting articles
- Processing information showing sources and timing

Be efficient but thorough. Focus on significance, accuracy, and readability."""

# Create news agent
def create_news_agent():
    return Agent(tools=NEWS_TOOLS, system_prompt=NEWS_PROMPT)

# Create news tool
def create_news_tool():
    return create_agent_tool(
        tools=NEWS_TOOLS,
        system_prompt=NEWS_PROMPT,
        tool_name="news_agent",
        tool_description="Autonomous news processing agent that fetches, categorizes, and summarizes daily news from multiple sources"
    )