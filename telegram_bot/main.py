import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from .handlers import start, help_command, info_command, echo_command, caps_command, echo_message, error_handler
from config import setup_development_logging, get_logger

# Load environment variables
load_dotenv()

# Set up colored logging
setup_development_logging()
logger = get_logger(__name__)

# Bot token - you'll need to get this from BotFather
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')



def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables!")
        print("Please set your bot token in a .env file or environment variable.")
        return
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("echo", echo_command))
    application.add_handler(CommandHandler("caps", caps_command))

    # Register message handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))

    # Register error handler
    application.add_error_handler(error_handler)

    print("Bot is starting...")
    print("Press Ctrl+C to stop the bot")
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()