from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.schema.messages import SystemMessage
import dotenv
import os

from .tool_regestery import register_tools
from .custom_parser import JSONCapableReActOutputParser
from config import setup_development_logging, get_logger

# Set up colored logging
setup_development_logging()
logger = get_logger(__name__)

dotenv.load_dotenv()

tools = register_tools()
logger.info(f"Registered {len(tools)} tools for the agent")

# Create memory for conversation history
memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    k=10  # Keep last 10 conversation turns
)
logger.debug("Initialized conversation memory with window size 10")

# Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.1
)
logger.info("Initialized Gemini LLM with temperature 0.1")

# Create a ReAct prompt template
react_prompt = PromptTemplate.from_template("""
You are Jeffry, a friendly personal assistant who replies in short, casual messages like a real person texting — no long essays, no formal tone. 
Keep responses natural, clear, and to the point.

You have access to tools to help answer questions and perform tasks.

You can use these tools:
{tools}

Follow this reasoning format when deciding what to do (this is your internal thinking, not what the user sees):

Question: the input question you must answer  
Thought: think step-by-step about the best approach  
Action: the action to take, must be one of [{tool_names}]  
Action Input: the input to the action (use valid JSON format for structured data)
Observation: the result of the action  
... (repeat Thought/Action/Action Input/Observation as needed)  
Thought: I now know the final answer  
Final Answer: short, casual reply to the user, based on your reasoning above.

Available tool tips:
- get_latest_messages: Use when asked for recent messages, news, or updates from Telegram channels
- schedule_task: Use to schedule reminders or future tasks - requires JSON with prompt, run_at, chat_id, task_name
- list_scheduled_tasks: Show all pending scheduled tasks
- cancel_scheduled_task: Cancel a task by its ID

Always use tools when they help.

Conversation so far:  
{chat_history}

Question: {input}  
Thought: {agent_scratchpad}
""")

# Create the ReAct agent with custom output parser
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=react_prompt,
    output_parser=JSONCapableReActOutputParser()
)
logger.info("Created ReAct agent successfully with custom JSON parser")

# Create the agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5
)
logger.info("Agent executor initialized and ready")