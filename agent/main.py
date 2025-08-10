from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.schema.messages import SystemMessage
import dotenv
import os

from .tool_regestery import register_tools
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
You are Jeffry, a helpful personal assistant. You have access to tools that can help answer questions and perform tasks.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Available tools:
- get_latest_messages: Use this when asked for recent messages, news, or updates from Telegram channels

Always try to use tools when they can help answer the question.

Previous conversation history:
{chat_history}

Question: {input}
Thought: {agent_scratchpad}
""")

# Create the ReAct agent
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=react_prompt
)
logger.info("Created ReAct agent successfully")

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