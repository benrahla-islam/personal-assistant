"""
Voice message processing module for Telegram bot.
Handles speech-to-text conversion using faster-whisper.
"""

from faster_whisper import WhisperModel
import tempfile
import os
import asyncio
from typing import Optional
from telegram import Bot
from config import get_logger

logger = get_logger(__name__)

# Load Whisper model once at module level
_whisper_model = None

def _get_whisper_model():
    """Get or load the Whisper model (lazy loading)."""
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading faster-whisper model (base)...")
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        logger.info("Faster-whisper model loaded successfully")
    return _whisper_model


async def transcribe_voice_message(file_id: str, bot: Bot) -> Optional[str]:
    """
    Download and transcribe a voice message from Telegram.
    
    Args:
        file_id: Telegram file ID of the voice message
        bot: Telegram Bot instance
        
    Returns:
        Transcribed text or None if transcription fails
    """
    temp_file_path = None
    
    try:
        logger.debug(f"Starting transcription for file_id: {file_id}")
        
        # Get file info from Telegram
        file = await bot.get_file(file_id)
        logger.debug(f"Got file info: {file.file_path}")
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            temp_file_path = temp_file.name
            logger.debug(f"Created temp file: {temp_file_path}")
        
        # Download the voice message
        await file.download_to_drive(temp_file_path)
        logger.debug(f"Downloaded voice message to: {temp_file_path}")
        
        # Transcribe using faster-whisper in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        model = _get_whisper_model()
        
        logger.debug("Starting faster-whisper transcription...")
        segments, info = await loop.run_in_executor(
            None, model.transcribe, temp_file_path
        )
        
        # Combine all segments into a single text
        transcribed_text = " ".join([segment.text for segment in segments]).strip()
        logger.info(f"Transcription completed: '{transcribed_text[:100]}...'")
        
        return transcribed_text if transcribed_text else None
        
    except Exception as e:
        logger.error(f"Error transcribing voice message {file_id}: {e}", exc_info=True)
        return None
        
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temp file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file: {cleanup_error}")


async def process_voice_message_with_agent(transcribed_text: str, agent, user_id: int, chat_id: int) -> str:
    """
    Process transcribed text through the agent and return response.
    
    Args:
        transcribed_text: The transcribed voice message text
        agent: The AI agent executor
        user_id: Telegram user ID
        chat_id: Telegram chat ID
        
    Returns:
        Agent response text
    """
    from datetime import datetime, timezone, timedelta
    
    try:
        logger.info(f"Processing transcribed text through agent for user {user_id}: '{transcribed_text[:50]}...'")
        
        # Prepare prompt with context
        utc_plus_1 = timezone(timedelta(hours=1))
        current_time = datetime.now(utc_plus_1)
        prompt = f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC+1 (Central European Time). From chat_id: {chat_id}, the user said via voice message: {transcribed_text}"
        
        # Invoke agent
        agent_response = agent.invoke({"input": prompt})
        logger.debug(f"Agent response type: {type(agent_response)}")
        
        # Extract response text
        response_text = _extract_agent_response(agent_response)
        
        # Limit response length
        if len(response_text) > 4000:
            response_text = response_text[:4000] + "... (message truncated)"
            logger.warning(f"Response truncated for user {user_id}")
        
        logger.info(f"Agent processing completed for user {user_id}")
        return response_text
        
    except Exception as e:
        logger.error(f"Error processing voice message through agent for user {user_id}: {e}", exc_info=True)
        
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
