"""
Shared helper for invoking the LangGraph agent.

Centralises rate-limiting, prompt formatting, response extraction, truncation,
and graceful error handling so that every call-site (text handler, voice handler,
scheduled tasks) behaves identically.
"""

from datetime import datetime, timezone, timedelta
from langchain_core.messages import HumanMessage
from config import get_logger

logger = get_logger(__name__)

# Maximum Telegram message length (Telegram supports 4096, leave margin)
MAX_RESPONSE_LENGTH = 4000


def invoke_agent(agent, message: str, user_id: int, chat_id: int) -> str:
    """
    Invoke the LangGraph agent with rate-limiting, prompt enrichment, and
    response extraction.

    Args:
        agent: The compiled LangGraph agent (``create_react_agent`` result).
        message: The raw user message (or scheduled-task prompt).
        user_id: Telegram user ID – used as the conversation thread ID.
        chat_id: Telegram chat ID – injected into the prompt so tools
                 (e.g. task scheduler) know where to reply.

    Returns:
        The agent's final text response, truncated to ``MAX_RESPONSE_LENGTH``.

    Raises:
        Re-raises any exception that is *not* a known LLM-parsing error.
    """
    from agent.rate_limiter import wait_for_rate_limit, get_rate_limiter

    logger.info(f"Processing message for user {user_id}: '{message[:100]}...'")

    try:
        # 1. Rate-limit
        logger.debug("⏳ Checking rate limits before API call...")
        wait_for_rate_limit()

        # 2. Enrich prompt with timestamp & chat context
        utc_plus_1 = timezone(timedelta(hours=1))
        current_time = datetime.now(utc_plus_1)
        prompt = (
            f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"UTC+1 (Central European Time). "
            f"From chat_id: {chat_id}, the user asked: {message}"
        )

        # 3. Invoke
        messages = [HumanMessage(content=prompt)]
        config = {"configurable": {"thread_id": str(user_id)}}
        agent_response = agent.invoke({"messages": messages}, config=config)

        # 4. Log rate-limit stats
        stats = get_rate_limiter().get_stats()
        logger.debug(
            f"📊 Rate limit: {stats['requests_last_minute']}/"
            f"{stats['max_requests_per_minute']} requests in last minute"
        )

        # 5. Extract final response text
        if agent_response and "messages" in agent_response:
            response_text = agent_response["messages"][-1].content
        else:
            response_text = "I'm having trouble processing that request."

        # 6. Truncate
        if len(response_text) > MAX_RESPONSE_LENGTH:
            response_text = response_text[:MAX_RESPONSE_LENGTH] + "... (message truncated)"
            logger.warning(f"Response truncated for user {user_id}")

        logger.info(f"Message processing completed for user {user_id}")
        return response_text

    except Exception as e:
        logger.error(f"Error processing message for user {user_id}: {e}", exc_info=True)

        # Handle known LLM-parsing errors gracefully
        if "Could not parse LLM output" in str(e):
            logger.warning("Attempting to extract response from parsing error")
            error_text = str(e)
            if "`" in error_text:
                start_idx = error_text.find("`") + 1
                end_idx = error_text.rfind("`")
                if start_idx > 0 and end_idx > start_idx:
                    extracted = error_text[start_idx:end_idx]
                    logger.info(f"Extracted response from parsing error for user {user_id}")
                    return extracted

        raise
