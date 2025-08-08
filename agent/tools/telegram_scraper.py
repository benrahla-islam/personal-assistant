import asyncio
from telegram_scraper.collector import TelethonChannelCollector
from llama_index.core.tools import FunctionTool
from llama_index.core.tools.types import ToolMetadata


async def fetch_messages_async() -> str:
    """Async function to fetch messages from Telegram channels."""
    collector = TelethonChannelCollector()
    
    # Start the client
    if not await collector.start_client():
        return "Failed to start Telegram client"
    
    try:
        # Fetch latest messages from followed channels
        channels = ['waslnews']
        
        all_messages = []
        for channel in channels:
            messages = await collector.get_recent_messages(channel, hours=24)
            for msg in messages[:5]:  # Get top 5 recent messages
                all_messages.append(f"📰 From @{channel}:\n{msg['text'][:200]}...\n📅 {msg['date']}\n👀 Views: {msg['views']}\n")
        
        if all_messages:
            return "\n" + "="*50 + "\n".join(all_messages)
        else:
            return "No recent messages found in followed channels."
            
    finally:
        await collector.close()


def get_latest_messages(request: str = "latest messages") -> str:
    """
    Get the latest messages from followed Telegram channels.
    
    Args:
        request: A description of what messages to fetch (e.g., "latest messages", "recent news")
        
    Returns:
        A formatted string containing the latest messages from followed channels
    """
    try:
        # Run the async function in a new event loop
        return asyncio.run(fetch_messages_async())
    except Exception as e:
        return f"Error fetching messages: {str(e)}"


get_latest_messages_tool = FunctionTool.from_defaults(
    name="get_latest_messages",
    description="Fetch the latest messages from followed Telegram channels.",
    fn=get_latest_messages,
)