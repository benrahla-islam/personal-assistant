from typing import List, Optional
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import asyncio
import os
import dotenv

from ..tools.tiktik_tool import tiktik_tool
from config import setup_development_logging, get_logger

dotenv.load_dotenv()
logger = get_logger(__name__)


class ReactAgent:
    def __init__(self, tools: Optional[List[Tool]] = None):
        self.tools = tools or []
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1
        )
        
        self.memory = MemorySaver()
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=self.memory
        )
        
        logger.info(f"ReactAgent initialized with {len(self.tools)} tools")
    
    def invoke(self, query: str, thread_id: str = "default") -> str:
        logger.debug(f"ReactAgent.invoke called with query: {query[:100]}...")
        config = {"configurable": {"thread_id": thread_id}}
        response = self.agent.invoke(
            {"messages": [HumanMessage(content=query)]},
            config=config
        )
        logger.debug(f"ReactAgent.invoke completed successfully")
        return response["messages"][-1].content
    
    async def ainvoke(self, query: str, thread_id: str = "default") -> str:
        logger.debug(f"ReactAgent.ainvoke called with query: {query[:100]}...")
        config = {"configurable": {"thread_id": thread_id}}
        response = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=query)]},
            config=config
        )
        logger.debug(f"ReactAgent.ainvoke completed successfully")
        return response["messages"][-1].content


def create_react_agent_tool() -> Tool:
    agent = ReactAgent()
    
    def react_func(query: str) -> str:
        return agent.invoke(query)
    
    return Tool(
        name="react_agent",
        description="Use for complex reasoning and problem-solving tasks",
        func=react_func
    )


async def create_react_agent_tool_async() -> Tool:
    agent = ReactAgent(tools=[tiktik_tool()])
    
    async def react_func_async(query: str) -> str:
        return await agent.ainvoke(query)
    
    return Tool(
        name="react_agent_async",
        description="Use for complex reasoning and problem-solving tasks (async)",
        func=react_func_async
    )