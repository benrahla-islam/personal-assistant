import asyncio
from telegram_scraper.collector import TelethonChannelCollector
from langchain.tools import tool


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


@tool
def get_latest_messages() -> str:
    """
    Get the latest messages from followed Telegram channels (used for news only).
    
    
    Returns:
        A formatted string containing the latest messages from followed channels (not working properly yet).
    """
    try:
        # Run the async function in a new event loop
        return asyncio.run(fetch_messages_async())
    except Exception as e:
        return f"Error fetching messages: {str(e)}"