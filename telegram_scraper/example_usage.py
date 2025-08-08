#!/usr/bin/env python3
"""
Example script showing how to use the TelethonChannelCollector
"""

import asyncio
import json
from collector import TelethonChannelCollector

async def main():
    """Main function demonstrating different use cases."""
    collector = TelethonChannelCollector()
    
    try:
        # Start the client
        if not await collector.start_client():
            print("Failed to start Telethon client. Check your credentials.")
            return
        
        print("Choose an option:")
        print("1. Get recent messages from a channel")
        print("2. Search for messages in a channel")
        print("3. Get channel information")
        print("4. Listen for new messages (real-time)")
        print("5. Get messages from multiple channels")
        print("6. Get messages after a specific date")
        print("7. Get messages between two dates")
        
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == "1":
            # Get recent messages
            channel = input("Enter channel username (without @): ").strip()
            limit = int(input("How many messages to fetch (default 10): ") or "10")
            
            print(f"\nFetching {limit} messages from @{channel}...")
            messages = await collector.get_messages_from_channel(channel, limit=limit)
            
            if messages:
                print(f"\nFound {len(messages)} messages:")
                for i, msg in enumerate(messages[:5], 1):  # Show first 5
                    print(f"\n--- Message {i} ---")
                    print(f"Date: {msg['date']}")
                    print(f"Text: {msg['text'][:200]}...")
                    print(f"Views: {msg['views']}")
                    print(f"Forwards: {msg['forwards']}")
            else:
                print("No messages found or error occurred.")
        
        elif choice == "2":
            # Search messages
            channel = input("Enter channel username (without @): ").strip()
            query = input("Enter search query: ").strip()
            limit = int(input("How many results to fetch (default 20): ") or "20")
            
            print(f"\nSearching for '{query}' in @{channel}...")
            messages = await collector.search_messages(channel, query, limit=limit)
            
            if messages:
                print(f"\nFound {len(messages)} messages:")
                for i, msg in enumerate(messages, 1):
                    print(f"\n--- Result {i} ---")
                    print(f"Date: {msg['date']}")
                    print(f"Text: {msg['text']}")
                    print(f"Views: {msg['views']}")
            else:
                print("No messages found or error occurred.")
        
        elif choice == "3":
            # Get channel info
            channel = input("Enter channel username (without @): ").strip()
            
            print(f"\nGetting info for @{channel}...")
            info = await collector.get_channel_info(channel)
            
            if info:
                print(f"\n--- Channel Information ---")
                print(f"Title: {info['title']}")
                print(f"Username: @{info['username']}")
                print(f"ID: {info['id']}")
                print(f"Participants: {info['participants_count']}")
                print(f"Description: {info['description']}")
                print(f"Is Broadcast: {info['is_broadcast']}")
                print(f"Is Megagroup: {info['is_megagroup']}")
            else:
                print("Could not get channel information.")
        
        elif choice == "4":
            # Listen for new messages
            channels_input = input("Enter channel usernames separated by commas: ").strip()
            channels = [ch.strip() for ch in channels_input.split(',')]
            
            print(f"\nListening for new messages from: {channels}")
            print("Press Ctrl+C to stop...")
            
            # Override the process_new_message method for custom handling
            async def custom_process_message(message_data, chat):
                print(f"\n🔔 NEW MESSAGE from @{chat.username or chat.title}")
                print(f"📅 Date: {message_data['date']}")
                print(f"💬 Text: {message_data['text'][:100]}...")
                print(f"👀 Views: {message_data['views']}")
                print("-" * 50)
            
            collector.process_new_message = custom_process_message
            await collector.listen_for_new_messages(channels)
        
        elif choice == "5":
            # Get messages from multiple channels
            channels_input = input("Enter channel usernames separated by commas: ").strip()
            channels = [ch.strip() for ch in channels_input.split(',')]
            limit = int(input("How many messages per channel (default 10): ") or "10")
            
            print(f"\nFetching messages from {len(channels)} channels...")
            all_messages = await collector.get_messages_from_multiple_channels(channels, limit)
            
            for channel, messages in all_messages.items():
                print(f"\n--- @{channel} ({len(messages)} messages) ---")
                for msg in messages[:3]:  # Show first 3 from each channel
                    print(f"  • {msg['text'][:80]}...")
        
        elif choice == "6":
            # Get messages after a specific date
            channel = input("Enter channel username (without @): ").strip()
            date_input = input("Enter date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS): ").strip()
            
            try:
                # Parse the date
                if ' ' in date_input:
                    after_date = collector.parse_date_string(date_input)
                else:
                    after_date = collector.parse_date_string(f"{date_input} 00:00:00")
                
                print(f"\nFetching messages from @{channel} after {after_date.isoformat()}...")
                messages = await collector.get_messages_after_date(channel, after_date)
                
                if messages:
                    print(f"\nFound {len(messages)} messages after {after_date.date()}:")
                    for i, msg in enumerate(messages[:10], 1):  # Show first 10
                        print(f"\n--- Message {i} ---")
                        print(f"Date: {msg['date']}")
                        print(f"Text: {msg['text'][:200]}...")
                        print(f"Views: {msg['views']}")
                else:
                    print("No messages found after the specified date.")
            except ValueError as e:
                print(f"Invalid date format: {e}")
                print("Please use format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")
        
        elif choice == "7":
            # Get messages between two dates
            channel = input("Enter channel username (without @): ").strip()
            start_date_input = input("Enter start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS): ").strip()
            end_date_input = input("Enter end date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS): ").strip()
            
            try:
                # Parse the dates
                if ' ' in start_date_input:
                    start_date = collector.parse_date_string(start_date_input)
                else:
                    start_date = collector.parse_date_string(f"{start_date_input} 00:00:00")
                
                if ' ' in end_date_input:
                    end_date = collector.parse_date_string(end_date_input)
                else:
                    end_date = collector.parse_date_string(f"{end_date_input} 23:59:59")
                
                print(f"\nFetching messages from @{channel} between {start_date.date()} and {end_date.date()}...")
                messages = await collector.get_messages_between_dates(channel, start_date, end_date)
                
                if messages:
                    print(f"\nFound {len(messages)} messages between the specified dates:")
                    for i, msg in enumerate(messages[:10], 1):  # Show first 10
                        print(f"\n--- Message {i} ---")
                        print(f"Date: {msg['date']}")
                        print(f"Text: {msg['text'][:200]}...")
                        print(f"Views: {msg['views']}")
                else:
                    print("No messages found in the specified date range.")
            except ValueError as e:
                print(f"Invalid date format: {e}")
                print("Please use format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")
        
        else:
            print("Invalid choice.")
    
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await collector.close()

if __name__ == "__main__":
    asyncio.run(main())
