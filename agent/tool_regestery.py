from .tools.telegram_scraper import get_latest_messages_tool


def register_tools(category = 'all'):
    if category == 'all':
        return [get_latest_messages_tool]
    return []