from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.gemini import Gemini
import dotenv

from .tool_regestery import register_tools

dotenv.load_dotenv()

tools = register_tools()

llm = Gemini(model="models/gemini-2.0-flash") 

agent = FunctionAgent(
    tools=tools,
    llm=llm,
    system_prompt=(
        "You are a helpful personal assistant. You have access to tools that can help users. "
        "When a user asks for information or help, analyze their request and use the appropriate tools. "
        "Available tools:\n"
        "- get_latest_messages: Use this when users ask for recent messages, news, or updates from Telegram channels\n"
        "Always try to use tools when they can help answer the user's question."
    )
)