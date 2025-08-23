from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import PromptTemplate
import dotenv
import os

from .tools.tool_regestery import register_tools
from .custom_parser import JSONCapableMRKLOutputParser
from config import setup_development_logging, get_logger

# Set up colored logging
setup_development_logging()
logger = get_logger(__name__)

dotenv.load_dotenv()

tools = register_tools()
logger.info(f"Registered {len(tools)} tools for the agent")

# Initialize the LLM with system instruction
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",  # Updated to latest available model
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.1,
    system_instruction="""You are Jeffry, a friendly personal assistant who replies in short, casual messages like a real person texting — no long essays, no formal tone. 
Keep responses natural, clear, and to the point.

You have access to tools to help answer questions and perform tasks. Always use tools when they can help answer the user's question or complete their request.

Available tool tips:
- get_latest_messages: Use when asked for recent messages, news, or updates from Telegram channels
- schedule_task: Use to schedule reminders or future tasks - requires JSON with prompt, run_at, chat_id, task_name
- list_scheduled_tasks: Show all pending scheduled tasks
- cancel_scheduled_task: Cancel a task by its ID"""
)
logger.info("Initialized Gemini LLM with system instruction and temperature 0.1")

# Create memory for conversation history (needs LLM for summarization)
memory = ConversationSummaryBufferMemory(
    llm=llm,
    memory_key="chat_history",
    return_messages=True,
    max_token_limit=10000,
    k=10  # Keep last 10 conversation turns
)

# Create a structured chat prompt template (MRKL-style reasoning)
mrkl_prompt = PromptTemplate.from_template("""
You are Jeffry, a friendly personal assistant who replies in short, casual messages. You have access to tools to help answer questions and perform tasks.

Respond to the human as helpfully and accurately as possible. You have access to the following tools:

{tools}

Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).

Valid "action" values: "Final Answer" or {tool_names}

Provide only ONE action per $JSON_BLOB, as shown:

```
{{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}}
```

Follow this format:

Question: input question to answer
Thought: consider previous and subsequent steps
Action:
```
{{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}}
```
Observation: action result
... (repeat Thought/Action/Observation N times)
Thought: I know what to respond
Action:
```
{{
  "action": "Final Answer",
  "action_input": "short, casual reply to the user"
}}
```

Conversation history:
{chat_history}

Question: {input}
Thought: {agent_scratchpad}
""")

# Create the structured chat agent (MRKL-style)
agent = create_structured_chat_agent(
    llm=llm,
    tools=tools,
    prompt=mrkl_prompt
)
logger.info("Created structured chat agent (MRKL-style) successfully")

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