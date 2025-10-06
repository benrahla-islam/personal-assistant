from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
import dotenv
import os
from pathlib import Path

from .tools.tool_regestery import register_tools
from config import setup_development_logging, get_logger

# Set up colored logging
setup_development_logging()
logger = get_logger(__name__)

dotenv.load_dotenv()

# System prompt for the agent
SYSTEM_PROMPT = """You are Jeffry, a friendly personal assistant who replies in short, casual messages like a real person texting — no long essays, no formal tone. 
Keep responses natural, clear, and to the point.

You have access to tools to help answer questions and perform tasks. Always use tools when they can help answer the user's question or complete their request.

Available tool tips:
- get_latest_messages: Use when asked for recent messages, news, or updates from Telegram channels
- schedule_task: Use to schedule reminders or future tasks - requires JSON with prompt, run_at, chat_id, task_name
- list_scheduled_tasks: Show all pending scheduled tasks
- cancel_scheduled_task: Cancel a task by its ID"""

# Initialize the main LLM for the primary agent
main_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # Best price-performance, optimized for agentic use cases
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.1,
    system_instruction=SYSTEM_PROMPT,  # This is the Gemini-specific way to set system prompt
    # Add rate limiting configurations
    request_timeout=30,  # 30 second timeout
    max_retries=2,  # Limit retries to avoid burning through quota
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
logger.info("Initialized specialized agents LLM with secondary API key")

# Register tools with specialized agents using secondary LLM
tools = register_tools(shared_llm=agents_llm)
logger.info(f"Registered {len(tools)} tools for the agent with distributed API keys")

# Create persistent memory with SQLite checkpoint
checkpoint_db_path = Path("agent_memory.db")
memory = MemorySaver()  # Use in-memory for now, can switch to SqliteSaver later
logger.info("Initialized persistent memory system")

# Create the modern LangGraph agent with memory using main LLM
agent = create_react_agent(
    model=main_llm,  # Main agent uses primary API key
    tools=tools,     # Tools use secondary API key (agents_llm)
    checkpointer=memory
)
logger.info("Created LangGraph ReAct agent with persistent memory")

class ModernAgentExecutor:
    """Modern agent executor wrapper with session management."""
    
    def __init__(self, agent, session_id: str = "default"):
        self.agent = agent
        self.session_id = session_id
        self.config = {"configurable": {"thread_id": session_id}}
        
        # Compatibility properties for existing tests
        self.tools = tools
        self.memory = memory
        self.verbose = True
        self.handle_parsing_errors = True
        self.max_iterations = 5
        self.return_intermediate_steps = False
    
    def invoke(self, inputs):
        """Execute the agent with session management."""
        if isinstance(inputs, dict) and "input" in inputs:
            message = inputs["input"]
        else:
            message = str(inputs)
        
        # Simple approach: always include system context in user message for now
        # This ensures personality while we get the memory working
        user_message = f"{message}"
        
        # The agent should maintain conversation history automatically via checkpointer
        # We just need to send the new user message
        messages = [HumanMessage(content=user_message)]
        
        # Invoke agent with session config - this should handle memory automatically
        result = self.agent.invoke(
            {"messages": messages},
            config=self.config
        )
        
        # Extract the final response
        if result and "messages" in result:
            final_message = result["messages"][-1]
            return {"output": final_message.content}
        
        return {"output": "I'm having trouble processing that request."}

# Create the agent executor with default session
agent_executor = ModernAgentExecutor(agent, session_id="personal_assistant_session")
logger.info("Modern agent executor initialized with session management")