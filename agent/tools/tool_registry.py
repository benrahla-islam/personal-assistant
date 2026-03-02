from .telegram_scraper import get_latest_messages
from .task_scheduler import schedule_task, list_scheduled_tasks, cancel_scheduled_task
from .extra_tools import search_tool, wiki_search_tool
from .planner_tools.todoist_tool import (
    todoist_add_tasks_tool,
    todoist_delete_task_tool,
    todoist_update_task_tool,
    todoist_get_tasks_by_date_tool
)
from ..specialized_agents.planner_agent import create_planner_tool
from ..specialized_agents.news_agent import create_news_tool
from .planner_tools.database_tools import get_database_tools


# ── Tool groups (each defined exactly once) ──────────────────────

TELEGRAM_TOOLS = [get_latest_messages]

SCHEDULER_TOOLS = [schedule_task, list_scheduled_tasks, cancel_scheduled_task]

SEARCH_TOOLS = [search_tool, wiki_search_tool]


def _todoist_tools():
    return [
        todoist_add_tasks_tool(),
        todoist_delete_task_tool(),
        todoist_update_task_tool(),
        todoist_get_tasks_by_date_tool(),
    ]


def _agent_tools(shared_llm):
    return [create_planner_tool(shared_llm), create_news_tool(shared_llm)]


# ── Category composition ────────────────────────────────────────

_CATEGORIES = {
    "telegram":  lambda llm: TELEGRAM_TOOLS,
    "scheduler": lambda llm: SCHEDULER_TOOLS,
    "database":  lambda llm: get_database_tools(),
    "todoist":   lambda llm: _todoist_tools(),
    "news":      lambda llm: [create_news_tool(llm)],
    "agents":    lambda llm: _agent_tools(llm),
    "planning":  lambda llm: (
        [create_planner_tool(llm)]
        + _todoist_tools()
        + SCHEDULER_TOOLS
        + get_database_tools()
    ),
}


def register_tools(category: str = "all", shared_llm=None) -> list:
    """
    Return a list of LangChain tools for the given category.

    Categories: all, telegram, scheduler, database, todoist, news, agents, planning.
    """
    if category in _CATEGORIES:
        return _CATEGORIES[category](shared_llm)

    # 'all' (default) — every tool group combined
    return (
        TELEGRAM_TOOLS
        + SCHEDULER_TOOLS
        + SEARCH_TOOLS
        + _agent_tools(shared_llm)
        + get_database_tools()
    )