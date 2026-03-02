from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, AIMessage
import dotenv
import os
from pathlib import Path

from .tools.tool_registry import register_tools
from .rate_limiter import wait_for_rate_limit, get_rate_limiter, configure_rate_limiter
from config import setup_development_logging, get_logger

# Set up colored logging
setup_development_logging()
logger = get_logger(__name__)

dotenv.load_dotenv()

# Configure rate limiter based on environment or use defaults
# Gemini free tier: 15 RPM (requests per minute)
# Setting min_delay to 4.0 seconds = max 15 requests/minute
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "4.0"))
RATE_LIMIT_MAX_RPM = int(os.getenv("RATE_LIMIT_MAX_RPM", "15"))

configure_rate_limiter(
    min_delay_seconds=RATE_LIMIT_DELAY,
    max_requests_per_minute=RATE_LIMIT_MAX_RPM
)
logger.info(f"Rate limiter configured: {RATE_LIMIT_DELAY}s delay, {RATE_LIMIT_MAX_RPM} requests/min")

# System prompt for the agent
SYSTEM_PROMPT = """You are Jeffry, a friendly personal assistant who replies in short, casual messages like a real person texting — no long essays, no formal tone. 
Keep responses natural, clear, and to the point.

You have access to tools to help answer questions and perform tasks. Always use tools when they can help answer the user's question or complete their request.

Available tool tips:
- get_latest_messages: Use when asked for recent messages, news, or updates from Telegram channels
- schedule_task: Use to schedule reminders or future tasks - requires JSON with prompt, run_at, chat_id, task_name
- list_scheduled_tasks: Show all pending scheduled tasks
- cancel_scheduled_task: Cancel a task by its ID"""


# ---------------------------------------------------------------------------
# Lazy initialization: LLM / tools / memory / agent are created on first use
# so that importing this module does NOT require a valid GOOGLE_API_KEY.
# ---------------------------------------------------------------------------
_agent = None
_agent_initialized = False


def _initialize_agent():
    """Create the LLM, register tools, open memory, and build the agent."""
    global _agent, _agent_initialized

    if _agent_initialized:
        return

    # Initialize the main LLM for the primary agent
    main_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.1,
        system_instruction=SYSTEM_PROMPT,
        request_timeout=30,
        max_retries=2,
    )
    logger.info("Initialized main Gemini LLM instance (API key 1)")

    # Initialize secondary LLM for specialized agents to distribute load
    agents_api_key = os.getenv("GOOGLE_API_KEY_AGENTS")
    if agents_api_key:
        agents_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=agents_api_key,
            temperature=0.1,
            request_timeout=30,
            max_retries=2,
        )
        logger.info("Initialized secondary Gemini LLM instance for specialized agents (API key 2)")
    else:
        agents_llm = main_llm
        logger.warning("No secondary API key found, specialized agents will use main LLM (shared quota)")

    # Register tools with specialized agents using secondary LLM
    tools = register_tools(shared_llm=agents_llm)
    logger.info(f"Registered {len(tools)} tools for the agent with distributed API keys")

    # Create persistent SQLite-based memory for conversation history
    checkpoint_db_path = "agent_memory.db"
    memory_conn = SqliteSaver.from_conn_string(checkpoint_db_path)
    memory = memory_conn.__enter__()
    logger.info(f"Initialized persistent SQLite memory at {checkpoint_db_path}")

    # Create the modern LangGraph agent with memory using main LLM
    _agent = create_react_agent(
        model=main_llm,
        tools=tools,
        checkpointer=memory,
    )
    _agent_initialized = True
    logger.info("Created LangGraph ReAct agent with persistent memory")


def get_agent():
    """Return the initialized agent, creating it on first call."""
    _initialize_agent()
    return _agent


# For backward-compatibility: module-level names that lazily initialize.
class _LazyAgent:
    """Proxy that defers agent creation until first attribute access / call."""

    def __getattr__(self, name):
        return getattr(get_agent(), name)

    def __call__(self, *args, **kwargs):
        return get_agent()(*args, **kwargs)

    # Support `invoke` directly (the most common usage)
    def invoke(self, *args, **kwargs):
        return get_agent().invoke(*args, **kwargs)


agent_executor = _LazyAgent()
agent = agent_executor  # alias