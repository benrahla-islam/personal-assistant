from .tools.telegram_scraper import get_latest_messages
from .tools.task_scheduler import schedule_task, list_scheduled_tasks, cancel_scheduled_task
from .tools.extra_tools import search_tool


def register_tools(category = 'all'):
    if category == 'all':
        return [
            get_latest_messages,
            schedule_task,
            list_scheduled_tasks,
            cancel_scheduled_task,
            search_tool
        ]
    elif category == 'telegram':
        return [get_latest_messages]
    elif category == 'scheduler':
        return [schedule_task, list_scheduled_tasks, cancel_scheduled_task]
    else:
        return [
            get_latest_messages,
            schedule_task,
            list_scheduled_tasks,
            cancel_scheduled_task,
            search_tool
        ]