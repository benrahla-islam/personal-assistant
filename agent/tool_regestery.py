from .tools.telegram_scraper import get_latest_messages


def register_tools(category = 'all'):
    if category == 'all':
        return [get_latest_messages]
    else :
        return [get_latest_messages]