from telegram_scraper.collector import TelethonChannelCollector
from llama_index.core.tools import FunctionTool
from llama_index.core.tools.types import ToolMetadata


def get_latest_messages(request: str = "latest messages") -> str:
    """
    Get the latest messages from followed Telegram channels.
    
    Args:
        request: A description of what messages to fetch (e.g., "latest messages", "recent news")
        
    Returns:
        A formatted string containing the latest messages from followed channels
    """
    try:
        collector = TelethonChannelCollector()
        collector.start_client()

        # Fetch latest messages from followed channels
        # For demonstration, we'll use a hardcoded list of channels
        channels = ['waslnews']
        # TODO: Replace with dynamic fetching of followed channels if needed
        
        all_messages = []
        for channel in channels:
            messages = collector.get_recent_messages(channel, hours=24)
            for msg in messages[:5]:  # Get top 5 recent messages
                all_messages.append(f"📰 From @{channel}:\n{msg['text'][:200]}...\n📅 {msg['date']}\n👀 Views: {msg['views']}\n")
        
        if all_messages:
            return "\n" + "="*50 + "\n".join(all_messages)
        else:
            return "No recent messages found in followed channels."
            
    except Exception as e:
        return f"Error fetching messages: {str(e)}"


get_latest_messages_tool = FunctionTool(
    fn=get_latest_messages,
    metadata=ToolMetadata(
        name="get_latest_messages",
        description="Fetches the latest messages and news from followed Telegram channels. Use this when users ask for recent news, updates, or messages from Telegram channels.",
    ),
)