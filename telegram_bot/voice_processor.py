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
    """
    from agent.agent_helpers import ainvoke_agent

    voice_prefix = "the user said via voice message: "
    return await ainvoke_agent(agent, voice_prefix + transcribed_text, user_id, chat_id)
