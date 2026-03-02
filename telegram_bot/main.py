import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from .handlers import echo_message, error_handler, voice_message_handler
from config import setup_bot_logging, get_logger
from config.settings import require_environment

# Load environment variables
load_dotenv()

# Set up bot-specific logging with minimal third-party noise
setup_bot_logging()
logger = get_logger(__name__)


def create_application() -> Application:
    """Create and configure the Telegram bot application."""
    # Fail fast if required env vars are missing
    require_environment()

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

    # Create the Application
    application = Application.builder().token(bot_token).build()

    # Register message handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    application.add_handler(MessageHandler(filters.VOICE, voice_message_handler))
    # Register error handler
    application.add_error_handler(error_handler)

    return application

def main() -> None:
    """Start the bot."""
    application = create_application()

    logger.info("Bot is starting...")
    print("Bot is starting...")
    print("Press Ctrl+C to stop the bot")
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()