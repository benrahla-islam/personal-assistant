from .telegram_scraper import get_latest_messages
from .task_scheduler import schedule_task, list_scheduled_tasks, cancel_scheduled_task
from .extra_tools import search_tool, wiki_search_tool
from .planner_tools.todoist_tool import (
    todoist_add_tasks_tool,
    todoist_delete_task_tool,
    todoist_update_task_tool,
    todoist_get_tasks_by_date_tool
)
from ..specialized_agents.planner_agent import (
    create_planner_tool,
    create_react_planner_tool
)
from .database_tools import get_database_tools


def register_tools(category = 'all'):
    if category == 'all':
        return [
            get_latest_messages,
            schedule_task,
            list_scheduled_tasks,
            cancel_scheduled_task,
            search_tool,
            wiki_search_tool,
            todoist_add_tasks_tool(),
            todoist_delete_task_tool(),
            todoist_update_task_tool(),
            todoist_get_tasks_by_date_tool(),
            create_planner_tool(),
            create_react_planner_tool()
        ] + get_database_tools()
    elif category == 'telegram':
        return [get_latest_messages]
    elif category == 'scheduler':
        return [schedule_task, list_scheduled_tasks, cancel_scheduled_task]
    elif category == 'database':
        return get_database_tools()
    elif category == 'todoist':
        return [
            todoist_add_tasks_tool(),
            todoist_delete_task_tool(),
            todoist_update_task_tool(),
            todoist_get_tasks_by_date_tool()
        ]
    elif category == 'planning':
        return [
            create_planner_tool(),
            create_react_planner_tool(),
            todoist_add_tasks_tool(),
            todoist_delete_task_tool(),
            todoist_update_task_tool(),
            todoist_get_tasks_by_date_tool(),
            schedule_task,
            list_scheduled_tasks,
            cancel_scheduled_task
        ] + get_database_tools()
    elif category == 'agents':
        return [
            create_planner_tool(),
            create_react_planner_tool()
        ]
    else:
        return [
            get_latest_messages,
            schedule_task,
            list_scheduled_tasks,
            cancel_scheduled_task,
            search_tool,
            wiki_search_tool,
            todoist_add_tasks_tool(),
            todoist_delete_task_tool(),
            todoist_update_task_tool(),
            todoist_get_tasks_by_date_tool(),
            create_planner_tool(),
            create_react_planner_tool()
        ] + get_database_tools()