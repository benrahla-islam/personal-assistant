from telegram import Update
from telegram.ext import ContextTypes
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}!\n\n"
        f"I'm your personal assistant bot. Here's what I can do:\n"
        f"• Send me any message and I'll echo it back\n"
        f"• Use /help to see available commands\n"
        f"• Use /info to get information about yourself"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
Available commands:

/start - Start the bot and see welcome message
/help - Show this help message
/info - Get your user information
/echo <message> - Echo back your message
/caps <message> - Convert your message to CAPS

Just send me any text message and I'll echo it back to you!
    """
    await update.message.reply_text(help_text)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send user information when the command /info is issued."""
    user = update.effective_user
    chat = update.effective_chat
    
    info_text = f"""
Your Information:
• Name: {user.full_name}
• Username: @{user.username if user.username else 'Not set'}
• User ID: {user.id}
• Chat ID: {chat.id}
• Chat Type: {chat.type}
    """
    await update.message.reply_text(info_text)

async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message after /echo command."""
    message_text = ' '.join(context.args)
    if message_text:
        await update.message.reply_text(f"Echo: {message_text}")
    else:
        await update.message.reply_text("Please provide a message to echo. Usage: /echo <message>")

async def caps_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Convert message to uppercase after /caps command."""
    message_text = ' '.join(context.args)
    if message_text:
        await update.message.reply_text(message_text.upper())
    else:
        await update.message.reply_text("Please provide a message to convert. Usage: /caps <message>")

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    user_message = update.message.text
    await update.message.reply_text(f"You said: {user_message}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)