"""
Shared helper for invoking the LangGraph agent.

Centralises rate-limiting, prompt formatting, response extraction, truncation,
and graceful error handling so that every call-site (text handler, voice handler,
scheduled tasks) behaves identically.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from langchain_core.messages import HumanMessage
from config import get_logger, settings
from .memory_pruner import prune_messages

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

        # 3. Handle Memory Pruning (Summarization)
        config = {"configurable": {"thread_id": str(user_id)}}
        state = agent.get_state(config)
        
        if state and state.values and "messages" in state.values:
            history = state.values["messages"]
            if len(history) > settings.MEMORY_PRUNE_THRESHOLD:
                from .main import get_llm
                llm = get_llm()
                pruned = prune_messages(history, llm, threshold=settings.MEMORY_PRUNE_THRESHOLD)
                
                # Check if pruning actually happened
                if len(pruned) < len(history):
                    # In LangGraph/ReAct agent, we can't easily "overwrite" the entire history 
                    # by just updating state messages due to the way Reducers work (they usually append).
                    # However, if we've summarized, we want to START fresh with the summary.
                    # For now, we'll try to update state, but a better approach for summaries 
                    # is often a custom graph with a filter/trimmer.
                    # Since we're wrapping, we'll use update_state.
                    agent.update_state(config, {"messages": pruned})
                    logger.info(f"Updated agent state with pruned history for user {user_id}")

        # 4. Invoke
        messages = [HumanMessage(content=prompt)]
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


async def ainvoke_agent(agent, message: str, user_id: int, chat_id: int) -> str:
    """Async version of invoke_agent."""
    from agent.rate_limiter import wait_for_rate_limit, get_rate_limiter

    logger.info(f"Processing message (async) for user {user_id}: '{message[:100]}...'")

    try:
        # 1. Rate-limit
        # wait_for_rate_limit() is sync, but we can run it in a thread or just call it 
        # (it's short sleeps if any). For true async, we'd want an async rate limiter.
        # But let's keep it simple for now as it's a 1-person project.
        await asyncio.to_thread(wait_for_rate_limit)

        # 2. Enrich prompt
        utc_plus_1 = timezone(timedelta(hours=1))
        current_time = datetime.now(utc_plus_1)
        prompt = (
            f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"UTC+1 (Central European Time). "
            f"From chat_id: {chat_id}, the user asked: {message}"
        )

        # 3. Pruning
        config = {"configurable": {"thread_id": str(user_id)}}
        state = await agent.aget_state(config)
        
        if state and state.values and "messages" in state.values:
            history = state.values["messages"]
            if len(history) > settings.MEMORY_PRUNE_THRESHOLD:
                from .main import get_llm
                llm = get_llm()
                # prune_messages uses llm.invoke (sync), let's use async if possible
                # for now keep it simple and just call it
                pruned = await asyncio.to_thread(prune_messages, history, llm, settings.MEMORY_PRUNE_THRESHOLD)
                if len(pruned) < len(history):
                    await agent.aupdate_state(config, {"messages": pruned})
                    logger.info(f"Updated agent state (async) with pruned history for user {user_id}")

        # 4. Invoke
        messages = [HumanMessage(content=prompt)]
        agent_response = await agent.ainvoke({"messages": messages}, config=config)

        # 5. Extract & Truncate
        if agent_response and "messages" in agent_response:
            response_text = agent_response["messages"][-1].content
        else:
            response_text = "I'm having trouble processing that request."

        if len(response_text) > MAX_RESPONSE_LENGTH:
            response_text = response_text[:MAX_RESPONSE_LENGTH] + "... (message truncated)"
            logger.warning(f"Response truncated for user {user_id}")

        return response_text

    except Exception as e:
        logger.error(f"Error in ainvoke_agent for user {user_id}: {e}", exc_info=True)
        # Mirror the extract-from-error logic if needed, but ainvoke is cleaner
        raise
