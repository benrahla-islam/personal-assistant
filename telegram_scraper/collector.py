import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, User, Message
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up colored logging
from config import setup_development_logging, get_logger
setup_development_logging()
logger = get_logger(__name__)

class TelethonChannelCollector:
    def __init__(self):
        """Initialize the Telethon client for collecting messages from channels."""
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')
        
        if not all([self.api_id, self.api_hash, self.phone_number]):
            raise ValueError("Missing required Telegram API credentials in environment variables")
        
        # Create the client
        self.client = TelegramClient('session_name', self.api_id, self.api_hash)
        
    async def start_client(self):
        """Start the Telegram client and handle authentication."""
        try:
            await self.client.start(phone=self.phone_number)
            logger.info("Telethon client started successfully")
            
            # Check if we're authorized
            if not await self.client.is_user_authorized():
                logger.warning("User not authorized. Please check your authentication.")
                return False
                
            # Get current user info
            me = await self.client.get_me()
            logger.info(f"Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
            return True
            
        except SessionPasswordNeededError:
            logger.error("Two-factor authentication enabled. Please enter your password.")
            # You might want to implement 2FA handling here
            return False
        except Exception as e:
            logger.error(f"Error starting client: {e}")
            return False
    
    async def get_channel_info(self, channel_username: str) -> Optional[Dict[str, Any]]:
        """Get information about a channel."""
        try:
            entity = await self.client.get_entity(channel_username)
            
            if isinstance(entity, Channel):
                return {
                    'id': entity.id,
                    'title': entity.title,
                    'username': entity.username,
                    'participants_count': entity.participants_count,
                    'description': entity.about if hasattr(entity, 'about') else None,
                    'is_broadcast': entity.broadcast,
                    'is_megagroup': entity.megagroup
                }
            else:
                logger.warning(f"{channel_username} is not a channel")
                return None
                
        except Exception as e:
            logger.error(f"Error getting channel info for {channel_username}: {e}")
            return None
    
    async def get_messages_from_channel(
        self, 
        channel_username: str, 
        limit: int = 100,
        offset_date: Optional[datetime] = None,
        min_id: int = 0,
        max_id: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a specific channel.
        
        Args:
            channel_username: Channel username (with or without @)
            limit: Maximum number of messages to retrieve
            offset_date: Get messages before this date
            min_id: Get messages with ID greater than this
            max_id: Get messages with ID less than this
        """
        try:
            # Clean channel username
            if channel_username.startswith('@'):
                channel_username = channel_username[1:]
            
            logger.info(f"Fetching messages from channel: @{channel_username}")
            
            messages = []
            async for message in self.client.iter_messages(
                channel_username,
                limit=limit,
                offset_date=offset_date,
                min_id=min_id,
                max_id=max_id
            ):
                message_data = await self._parse_message(message)
                if message_data:
                    messages.append(message_data)
            
            logger.info(f"Retrieved {len(messages)} messages from @{channel_username}")
            return messages
            
        except FloodWaitError as e:
            logger.warning(f"Flood wait error: need to wait {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return []
        except Exception as e:
            logger.error(f"Error fetching messages from {channel_username}: {e}")
            return []
    
    async def get_messages_from_multiple_channels(
        self, 
        channel_usernames: List[str], 
        limit_per_channel: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get messages from multiple channels."""
        all_messages = {}
        
        for channel in channel_usernames:
            logger.info(f"Processing channel: {channel}")
            messages = await self.get_messages_from_channel(channel, limit_per_channel)
            all_messages[channel] = messages
            
            # Small delay to avoid hitting rate limits
            await asyncio.sleep(1)
        
        return all_messages
    
    async def get_recent_messages(
        self, 
        channel_username: str, 
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get messages from the last N hours."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return await self.get_messages_after_date(channel_username, cutoff_time)
    
    async def get_messages_after_date(
        self,
        channel_username: str,
        after_date: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a channel that were published after a specific date.
        
        Args:
            channel_username: Channel username (with or without @)
            after_date: Only get messages published after this date
            limit: Maximum number of messages to check (default 1000)
        
        Returns:
            List of messages published after the specified date
        """
        try:
            # Clean channel username
            if channel_username.startswith('@'):
                channel_username = channel_username[1:]
            
            logger.info(f"Fetching messages from @{channel_username} after {after_date.isoformat()}")
            
            messages = []
            message_count = 0
            
            async for message in self.client.iter_messages(
                channel_username,
                limit=limit
            ):
                message_count += 1
                
                # Check if message is after the specified date
                if message.date > after_date:
                    message_data = await self._parse_message(message)
                    if message_data:
                        messages.append(message_data)
                else:
                    # Since messages are ordered from newest to oldest,
                    # if we encounter a message older than our cutoff date,
                    # we can stop searching
                    logger.info(f"Reached messages older than {after_date.isoformat()}, stopping search")
                    break
            
            logger.info(f"Retrieved {len(messages)} messages from @{channel_username} after {after_date.isoformat()}")
            logger.info(f"Checked {message_count} total messages")
            return messages
            
        except FloodWaitError as e:
            logger.warning(f"Flood wait error: need to wait {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return []
        except Exception as e:
            logger.error(f"Error fetching messages from {channel_username} after date: {e}")
            return []
    
    async def get_messages_between_dates(
        self,
        channel_username: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a channel between two specific dates.
        
        Args:
            channel_username: Channel username (with or without @)
            start_date: Get messages after this date
            end_date: Get messages before this date
            limit: Maximum number of messages to check
        
        Returns:
            List of messages between the specified dates
        """
        try:
            # Clean channel username
            if channel_username.startswith('@'):
                channel_username = channel_username[1:]
            
            logger.info(f"Fetching messages from @{channel_username} between {start_date.isoformat()} and {end_date.isoformat()}")
            
            messages = []
            message_count = 0
            
            async for message in self.client.iter_messages(
                channel_username,
                limit=limit,
                offset_date=end_date  # Start from end_date and go backwards
            ):
                message_count += 1
                
                # Check if message is within our date range
                if start_date <= message.date <= end_date:
                    message_data = await self._parse_message(message)
                    if message_data:
                        messages.append(message_data)
                elif message.date < start_date:
                    # We've gone too far back, stop searching
                    logger.info(f"Reached messages older than {start_date.isoformat()}, stopping search")
                    break
            
            # Sort messages by date (oldest first)
            messages.sort(key=lambda x: x['date'])
            
            logger.info(f"Retrieved {len(messages)} messages from @{channel_username} between dates")
            logger.info(f"Checked {message_count} total messages")
            return messages
            
        except FloodWaitError as e:
            logger.warning(f"Flood wait error: need to wait {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return []
        except Exception as e:
            logger.error(f"Error fetching messages from {channel_username} between dates: {e}")
            return []
    
    async def _parse_message(self, message: Message) -> Optional[Dict[str, Any]]:
        """Parse a Telegram message into a dictionary."""
        if not message:
            return None
        
        try:
            # Get sender information
            sender = await message.get_sender()
            sender_info = {}
            
            if isinstance(sender, User):
                sender_info = {
                    'type': 'user',
                    'id': sender.id,
                    'first_name': sender.first_name,
                    'last_name': sender.last_name,
                    'username': sender.username
                }
            elif isinstance(sender, Channel):
                sender_info = {
                    'type': 'channel',
                    'id': sender.id,
                    'title': sender.title,
                    'username': sender.username
                }
            
            return {
                'id': message.id,
                'text': message.text or '',  # Handle messages without text
                'date': message.date.isoformat(),
                'sender': sender_info,
                'views': message.views,
                'forwards': message.forwards,
                'replies': message.replies.replies if message.replies else 0,
                'is_reply': message.is_reply,
                'reply_to_msg_id': message.reply_to_msg_id,
                'media': bool(message.media),
                'media_type': type(message.media).__name__ if message.media else None,
                'edit_date': message.edit_date.isoformat() if message.edit_date else None,
                'grouped_id': message.grouped_id,
                'from_scheduled': message.from_scheduled
            }
            
        except Exception as e:
            logger.error(f"Error parsing message {message.id}: {e}")
            return None
    
    def parse_date_string(self, date_string: str) -> datetime:
        """
        Parse various date string formats into datetime objects.
        
        Supported formats:
        - ISO format: "2025-08-08T12:00:00"
        - Date only: "2025-08-08"
        - With timezone: "2025-08-08 12:00:00+00:00"
        """
        try:
            # Try different date formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S%z"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            # If no format matches, raise an error
            raise ValueError(f"Unable to parse date string: {date_string}")
            
        except Exception as e:
            logger.error(f"Error parsing date string '{date_string}': {e}")
            raise
    
    async def listen_for_new_messages(self, channel_usernames: List[str]):
        """Listen for new messages in real-time from specified channels."""
        logger.info(f"Starting to listen for new messages from: {channel_usernames}")
        
        @self.client.on(events.NewMessage(chats=channel_usernames))
        async def new_message_handler(event):
            message_data = await self._parse_message(event.message)
            if message_data:
                logger.info(f"New message from {event.chat.username or event.chat.title}: {message_data['text'][:100]}...")
                # Here you can process the new message as needed
                await self.process_new_message(message_data, event.chat)
        
        logger.info("Listening for new messages... Press Ctrl+C to stop")
        await self.client.run_until_disconnected()
    
    async def process_new_message(self, message_data: Dict[str, Any], chat):
        """Process new messages as they arrive. Override this method for custom processing."""
        # Example processing - you can customize this
        print(f"\n--- New Message ---")
        print(f"From: {chat.username or chat.title}")
        print(f"Text: {message_data['text']}")
        print(f"Date: {message_data['date']}")
        print(f"Views: {message_data['views']}")
        print("------------------\n")
    
    async def search_messages(
        self, 
        channel_username: str, 
        query: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for specific messages in a channel."""
        try:
            logger.info(f"Searching for '{query}' in @{channel_username}")
            
            messages = []
            async for message in self.client.iter_messages(
                channel_username,
                search=query,
                limit=limit
            ):
                message_data = await self._parse_message(message)
                if message_data:
                    messages.append(message_data)
            
            logger.info(f"Found {len(messages)} messages matching '{query}'")
            return messages
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []
    
    async def close(self):
        """Close the Telegram client."""
        await self.client.disconnect()
        logger.info("Telethon client disconnected")

# Example usage functions
async def example_get_channel_messages():
    """Example: Get messages from a channel."""
    collector = TelethonChannelCollector()
    
    try:
        if await collector.start_client():
            # Get messages from a channel
            messages = await collector.get_messages_from_channel(
                'channelname',  # Replace with actual channel username
                limit=10
            )
            
            for msg in messages:
                print(f"Message: {msg['text'][:100]}...")
                print(f"Date: {msg['date']}")
                print(f"Views: {msg['views']}")
                print("-" * 50)
                
    finally:
        await collector.close()

async def example_get_messages_after_date():
    """Example: Get messages published after a specific date."""
    collector = TelethonChannelCollector()
    
    try:
        if await collector.start_client():
            # Define the cutoff date
            after_date = datetime(2025, 8, 1, 0, 0, 0)  # August 1, 2025
            
            # Get messages from a channel after the specified date
            messages = await collector.get_messages_after_date(
                'channelname',  # Replace with actual channel username
                after_date
            )
            
            print(f"Found {len(messages)} messages after {after_date.isoformat()}")
            for msg in messages:
                print(f"Message: {msg['text'][:100]}...")
                print(f"Date: {msg['date']}")
                print(f"Views: {msg['views']}")
                print("-" * 50)
                
    finally:
        await collector.close()

async def example_get_messages_between_dates():
    """Example: Get messages between two specific dates."""
    collector = TelethonChannelCollector()
    
    try:
        if await collector.start_client():
            # Define date range
            start_date = datetime(2025, 8, 1, 0, 0, 0)   # August 1, 2025
            end_date = datetime(2025, 8, 7, 23, 59, 59)  # August 7, 2025
            
            # Get messages from a channel between the specified dates
            messages = await collector.get_messages_between_dates(
                'channelname',  # Replace with actual channel username
                start_date,
                end_date
            )
            
            print(f"Found {len(messages)} messages between {start_date.date()} and {end_date.date()}")
            for msg in messages:
                print(f"Message: {msg['text'][:100]}...")
                print(f"Date: {msg['date']}")
                print(f"Views: {msg['views']}")
                print("-" * 50)
                
    finally:
        await collector.close()

async def example_listen_for_new_messages():
    """Example: Listen for new messages in real-time."""
    collector = TelethonChannelCollector()
    
    try:
        if await collector.start_client():
            # List of channels to monitor
            channels = ['channel1', 'channel2']  # Replace with actual channel usernames
            await collector.listen_for_new_messages(channels)
            
    finally:
        await collector.close()

async def example_search_messages():
    """Example: Search for specific messages."""
    collector = TelethonChannelCollector()
    
    try:
        if await collector.start_client():
            # Search for messages containing specific keywords
            messages = await collector.search_messages(
                'channelname',  # Replace with actual channel username
                'keyword',      # Replace with search term
                limit=20
            )
            
            for msg in messages:
                print(f"Found: {msg['text']}")
                print(f"Date: {msg['date']}")
                print("-" * 50)
                
    finally:
        await collector.close()

if __name__ == "__main__":
    # Uncomment the example you want to run
    # asyncio.run(example_get_channel_messages())
    # asyncio.run(example_listen_for_new_messages())
    # asyncio.run(example_search_messages())
    pass