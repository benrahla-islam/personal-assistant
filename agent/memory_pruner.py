"""
Utility for pruning and summarizing LangGraph thread history.
Keeps context windows short by condensing older messages into a summary.
"""

from typing import List, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from config import get_logger, settings

logger = get_logger(__name__)

def get_history_summary(messages: Sequence[BaseMessage], llm) -> str:
    """
    Summarize a sequence of messages into a single string.
    """
    if not messages:
        return ""
        
    # Format the messages for the summarizer
    formatted_history = ""
    for msg in messages:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        formatted_history += f"{role}: {msg.content}\n"
        
    summary_prompt = (
        f"Please provide a concise but comprehensive summary of the following conversation history. "
        f"Preserve all key facts, names, decisions, and context. "
        f"History:\n{formatted_history}\n\nSummary:"
    )
    
    response = llm.invoke([HumanMessage(content=summary_prompt)])
    return response.content

def prune_messages(messages: List[BaseMessage], llm, threshold: int = 20) -> List[BaseMessage]:
    """
    If the number of messages exceeds the threshold, summarize the oldest ones.
    Keeps the last 6 messages (3 turns) as raw history.
    """
    if len(messages) <= threshold:
        return messages
        
    logger.info(f"Pruning history: {len(messages)} messages exceeds threshold of {threshold}")
    
    # We always keep the last N messages for immediate context
    # And we summarize everything before that.
    # Note: If messages[0] is a SystemMessage, we might want to keep it or handle it separately.
    
    # We keep a few recent messages for immediate context.
    # Defaulting to 6 (about 3 turns), but not more than the threshold.
    keep_count = min(6, threshold)
    to_summarize = messages[:-keep_count]
    to_keep = messages[-keep_count:]
    
    summary_text = get_history_summary(to_summarize, llm)
    
    summary_message = SystemMessage(
        content=f"Summary of previous conversation: {summary_text}"
    )
    
    # Return the summary followed by the recent messages
    pruned = [summary_message] + to_keep
    
    logger.info(f"History pruned: {len(messages)} -> {len(pruned)} messages")
    return pruned
