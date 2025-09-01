"""
Simple agent blueprint - one class that does everything.
"""

from typing import List, Optional
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import os
import dotenv
from config import get_logger

dotenv.load_dotenv()
logger = get_logger(__name__)


class Agent:
    """Simple agent that can do everything."""
    
    def __init__(
        self, 
        tools: Optional[List[Tool]] = None,
        system_prompt: str = "You are a helpful AI assistant.",
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.1
    ):
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=self.temperature
        )
        
        # Initialize memory and agent
        self.memory = MemorySaver()
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=self.memory
        )
        
        logger.info(f"Agent initialized with {len(self.tools)} tools")
    
    def invoke(self, query: str, thread_id: str = "default") -> str:
        """Execute the agent with a query."""
        messages = [HumanMessage(content=f"{self.system_prompt}\n\nUser: {query}")]
        config = {"configurable": {"thread_id": thread_id}}
        response = self.agent.invoke({"messages": messages}, config=config)
        return response["messages"][-1].content
    
    async def ainvoke(self, query: str, thread_id: str = "default") -> str:
        """Execute the agent async."""
        messages = [HumanMessage(content=f"{self.system_prompt}\n\nUser: {query}")]
        config = {"configurable": {"thread_id": thread_id}}
        response = await self.agent.ainvoke({"messages": messages}, config=config)
        return response["messages"][-1].content


def create_agent_tool(
    tools: List[Tool],
    system_prompt: str,
    tool_name: str,
    tool_description: str,
    model: str = "gemini-2.0-flash-exp",
    temperature: float = 0.1,
    async_mode: bool = False
) -> Tool:
    """
    Create a tool from an agent with custom parameters.
    
    Args:
        tools: Tools for the agent
        system_prompt: Instructions for the agent  
        tool_name: Name of the resulting tool
        tool_description: Description of the tool
        model: LLM model to use
        temperature: Response randomness
        async_mode: Use async or sync
    """
    agent = Agent(
        tools=tools,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature
    )
    
    if async_mode:
        async def tool_func(query: str) -> str:
            return await agent.ainvoke(query)
    else:
        def tool_func(query: str) -> str:
            return agent.invoke(query)
    
    return Tool(
        name=tool_name,
        description=tool_description,
        func=tool_func
    )