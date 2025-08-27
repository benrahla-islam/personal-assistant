from telegram import Update
from telegram.ext import ContextTypes
import logging
from datetime import datetime, timezone, timedelta
# Set up colored logging
from config import setup_development_logging, get_logger
from .voice_processor import transcribe_voice_message, process_voice_message_with_agent

setup_development_logging()
logger = get_logger(__name__)

# Import agent with logging
try:
    logger.info("Importing agent module...")
    from agent.main import agent_executor as agent
    logger.info(f"Agent imported successfully. Type: {type(agent)}")
    logger.info(f"Agent attributes: {[attr for attr in dir(agent) if not attr.startswith('_')]}")
except Exception as e:
    logger.error(f"Failed to import agent: {e}", exc_info=True)
    agent = None


async def process_text_message(user_message: str, user_id: int, chat_id: int, agent) -> str:
    """
    Process a text message through the agent and return the response.
    
    Args:
        user_message: The user's text message
        user_id: Telegram user ID  
        chat_id: Telegram chat ID
        agent: The AI agent executor
        
    Returns:
        Agent response text
    """
    logger.info(f"Processing text message from user {user_id}: '{user_message[:100]}...'")
    
    try:
        # Use UTC+1 timezone (Central European Time)
        utc_plus_1 = timezone(timedelta(hours=1))
        current_time = datetime.now(utc_plus_1)
        prompt = f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC+1 (Central European Time). From chat_id: {chat_id}, the user asked: {user_message}"
        
        agent_response = agent.invoke({"input": prompt})
        logger.debug(f"Got agent response: {type(agent_response)}")
        
        # Extract response text using the same logic as voice processor
        response_text = _extract_agent_response(agent_response)
        
        # Limit response length
        if len(response_text) > 4000:
            response_text = response_text[:4000] + "... (message truncated)"
            logger.warning(f"Response truncated for user {user_id}")
        
        logger.info(f"Text message processing completed for user {user_id}")
        return response_text
        
    except Exception as e:
        logger.error(f"Error processing text message for user {user_id}: {e}", exc_info=True)
        
        # Handle parsing errors gracefully
        if "Could not parse LLM output" in str(e):
            logger.warning("Attempting to extract response from parsing error")
            error_text = str(e)
            if "`" in error_text:
                start_idx = error_text.find("`") + 1
                end_idx = error_text.rfind("`")
                if start_idx > 0 and end_idx > start_idx:
                    extracted_response = error_text[start_idx:end_idx]
                    logger.info(f"Extracted response from parsing error for user {user_id}")
                    return extracted_response
        
        raise e


def _extract_agent_response(agent_response) -> str:
    """Extract text response from various agent response formats."""
    
    # Handle AgentFinish (final response)
    if hasattr(agent_response, 'return_values') and hasattr(agent_response, 'log'):
        if isinstance(agent_response.return_values, dict) and 'output' in agent_response.return_values:
            return agent_response.return_values['output']
        else:
            return str(agent_response.return_values)
    
    # Handle dict with 'output' key
    elif isinstance(agent_response, dict) and 'output' in agent_response:
        return str(agent_response['output'])
    
    # Handle objects with common response attributes
    elif hasattr(agent_response, 'content'):
        return str(agent_response.content)
    elif hasattr(agent_response, 'response'):
        return str(agent_response.response)
    elif hasattr(agent_response, 'text'):
        return str(agent_response.text)
    elif hasattr(agent_response, 'message'):
        return str(agent_response.message)
    
    # Fallback to string conversion
    else:
        return str(agent_response)


async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process user message with the agent."""
    user_message = update.message.text
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Check if agent is available
    if agent is None:
        logger.error("Agent is not available - import failed")
        await update.message.reply_text(
            "Sorry, the AI agent is not available right now. Please try again later."
        )
        return
    
    try:
        # Send a "thinking" message to show the bot is processing
        thinking_message = await update.message.reply_text("🤔 Thinking...")
        logger.debug(f"Sent thinking message to user {user_id}")
        
        # Process the text message through the agent
        response_text = await process_text_message(user_message, user_id, chat_id, agent)
        
        # Send the response
        logger.debug(f"Sending final response to user {user_id}")
        try:
            # Try to send with Markdown formatting first
            await thinking_message.edit_text(response_text, parse_mode='Markdown')
            logger.info(f"Successfully sent formatted response to user {user_id}")
        except Exception as format_error:
            logger.warning(f"Markdown formatting failed, sending as plain text: {format_error}")
            # Fallback to plain text if Markdown fails
            await thinking_message.edit_text(response_text)
            logger.info(f"Successfully sent plain text response to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing message with agent for user {user_id}: {e}", exc_info=True)
        
        try:
            await update.message.reply_text(
                "Sorry, I encountered an error while processing your message. "
                f"Error details: {str(e)[:200]}"
            )
            logger.info(f"Sent error message to user {user_id}")
        except Exception as reply_error:
            logger.error(f"Failed to send error message to user {user_id}: {reply_error}")


async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice messages by transcribing and processing them."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    logger.info(f"Received voice message from user {user_id}")

    # Check if agent is available
    if agent is None:
        logger.error("Agent is not available - import failed")
        await update.message.reply_text(
            "Sorry, the AI agent is not available right now. Please try again later."
        )
        return

    # Get the voice message file ID
    voice_file_id = update.effective_message.voice.file_id

    try:
        # Send a "transcribing" message
        processing_message = await update.message.reply_text("🎙️ Transcribing voice message...")
        logger.debug(f"Sent transcribing message to user {user_id}")

        # Transcribe the voice message
        transcribed_text = await transcribe_voice_message(voice_file_id, context.bot)
        
        if not transcribed_text:
            await processing_message.edit_text(
                "Sorry, I couldn't understand your voice message. Please try again or send a text message."
            )
            return

        logger.info(f"Transcription for user {user_id}: '{transcribed_text[:100]}...'")
        
        # Update message to show processing
        await processing_message.edit_text("🤔 Processing your message...")
        
        # Process the transcribed text through the agent
        response_text = await process_voice_message_with_agent(
            transcribed_text, agent, user_id, chat_id
        )
        
        # Send the final response
        try:
            await processing_message.edit_text(
                f"🎙️ **Voice Message:** {transcribed_text}\n\n{response_text}",
                parse_mode='Markdown'
            )
            logger.info(f"Successfully sent voice response to user {user_id}")
        except Exception as format_error:
            logger.warning(f"Markdown formatting failed, sending as plain text: {format_error}")
            await processing_message.edit_text(
                f"🎙️ Voice Message: {transcribed_text}\n\n{response_text}"
            )
            logger.info(f"Successfully sent plain text voice response to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing voice message from user {user_id}: {e}", exc_info=True)
        try:
            await update.message.reply_text(
                "Sorry, I couldn't process your voice message. "
                f"Error details: {str(e)[:200]}"
            )
        except Exception as reply_error:
            logger.error(f"Failed to send error message to user {user_id}: {reply_error}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("=" * 50)
    logger.error("TELEGRAM BOT ERROR HANDLER TRIGGERED")
    logger.error("=" * 50)
    
    # Log the error details
    if context.error:
        logger.error(f"Error type: {type(context.error)}")
        logger.error(f"Error message: {context.error}")
        logger.error(f"Error args: {getattr(context.error, 'args', 'No args')}")
        logger.error("Full traceback:", exc_info=context.error)
    
    # Log update details if available
    if update:
        logger.error(f"Update type: {type(update)}")
        if hasattr(update, 'effective_user') and update.effective_user:
            logger.error(f"User ID: {update.effective_user.id}")
            logger.error(f"Username: {update.effective_user.username}")
        if hasattr(update, 'effective_message') and update.effective_message:
            logger.error(f"Message text: {getattr(update.effective_message, 'text', 'No text')}")
    
    logger.error("=" * 50)