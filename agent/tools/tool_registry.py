from typing import List, Callable, Dict, Union
from config import get_logger

logger = get_logger(__name__)

# Registry of tools categorized by group name
# Format: {category: [tool_function_or_instance, ...]}
_TOOL_REGISTRY: Dict[str, List[Union[Callable, object]]] = {}

def register_tool(category: str):
    """
    Decorator to register a tool into a specific category.
    Usage:
        @register_tool("telegram")
        def some_tool(input): ...
    """
    def decorator(tool):
        if category not in _TOOL_REGISTRY:
            _TOOL_REGISTRY[category] = []
        _TOOL_REGISTRY[category].append(tool)
        return tool
    return decorator

def get_registered_tools(category: str) -> List:
    """Return all tools registered in a category."""
    return _TOOL_REGISTRY.get(category, [])

# ── Dynamic Tool Loading ────────────────────────────────────────

# For tools that require LLM or dynamic creation, we keep the lambdas
# but they will now also pull from the registry where possible.

def get_todoist_tools():
    from .planner_tools.todoist_tool import (
        todoist_add_tasks_tool, todoist_delete_task_tool,
        todoist_update_task_tool, todoist_get_tasks_by_date_tool
    )
    return [
        todoist_add_tasks_tool(), todoist_delete_task_tool(),
        todoist_update_task_tool(), todoist_get_tasks_by_date_tool()
    ]

def get_agent_tools(shared_llm):
    from ..specialized_agents.planner_agent import create_planner_tool
    from ..specialized_agents.news_agent import create_news_tool
    return [create_planner_tool(shared_llm), create_news_tool(shared_llm)]

def get_database_tools_wrapper():
    from .planner_tools.database_tools import get_database_tools
    return get_database_tools()

# Category composition
_CATEGORIES = {
    "telegram":  lambda llm: get_registered_tools("telegram"),
    "scheduler": lambda llm: get_registered_tools("scheduler"),
    "database":  lambda llm: get_database_tools_wrapper(),
    "todoist":   lambda llm: get_todoist_tools(),
    "news":      lambda llm: get_registered_tools("news") or [get_agent_tools(llm)[1]],
    "agents":    lambda llm: get_agent_tools(llm),
    "search":    lambda llm: get_registered_tools("search"),
    "planning":  lambda llm: (
        [get_agent_tools(llm)[0]]
        + get_todoist_tools()
        + get_registered_tools("scheduler")
        + get_database_tools_wrapper()
    ),
}

def register_tools(category: str = "all", shared_llm=None) -> list:
    """
    Return a list of LangChain tools for the given category.
    Categories: all, telegram, scheduler, database, todoist, news, agents, planning.
    """
    # Trigger imports of tools so they register themselves
    from . import telegram_scraper, task_scheduler, extra_tools
    
    if category in _CATEGORIES:
        return _CATEGORIES[category](shared_llm)

    # 'all' (default) — every tool group combined
    all_tools = []
    # Add registered tools from known categories
    for cat in ["telegram", "scheduler", "search"]:
        all_tools.extend(get_registered_tools(cat))
    
    # Add dynamic tools
    all_tools.extend(get_agent_tools(shared_llm))
    all_tools.extend(get_database_tools_wrapper())
    
    return all_tools