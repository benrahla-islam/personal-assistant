import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from .handlers import echo_message, error_handler, voice_message_handler
from config import setup_bot_logging, get_logger

# Load environment variables
load_dotenv()

# Set up bot-specific logging with minimal third-party noise
setup_bot_logging()
logger = get_logger(__name__)

# Bot token - you'll need to get this from BotFather
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def create_application() -> Application:
    """Create and configure the Telegram bot application."""
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables!")
        print("Please set your bot token in a .env file or environment variable.")
        return
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register message handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    application.add_handler(MessageHandler(filters.VOICE, voice_message_handler))  # Handle voice messages
    # Register error handler
    application.add_error_handler(error_handler)

    return application

def main() -> None:
    """Start the bot."""
    application = create_application()

    print("Bot is starting...")
    print("Press Ctrl+C to stop the bot")
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()