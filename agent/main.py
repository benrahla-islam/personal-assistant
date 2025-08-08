from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.memory import Memory
from llama_index.llms.gemini import Gemini
import dotenv

from .tool_regestery import register_tools

dotenv.load_dotenv()

tools = register_tools()

memory = Memory.from_defaults(session_id="personal_assistant_session", token_limit=10248)

llm = Gemini(model="models/gemini-2.0-flash") 

agent = ReActAgent(
    name='Jeffry',
    description="A helpful personal assistant that can answer questions and perform tasks using available tools.",
    tools=tools,
    llm=llm,
    system_prompt=(
        "You are a helpful personal assistant. You have access to tools that can help me. "
        "When I ask for information or help, analyze my request and use the appropriate tools. "
        "Available tools:\n"
        "- get_latest_messages: Use this when I ask for recent messages, news, or updates from Telegram channels\n"
        "Always try to use tools when they can help answer my question."
    ),
    memory=memory
)