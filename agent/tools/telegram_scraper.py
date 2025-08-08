from telegram_scraper import TelethonChannelCollector
from llama_index.core.tools import FunctionTool
from llama_index.core.tools.types import ToolMetadata


def get_latest_messages():
    collector = TelethonChannelCollector()
    return collector.get_latest_messages()


get_latest_messages_tool = FunctionTool(
    func=get_latest_messages,
    metadata=ToolMetadata(
        name="get_latest_messages",
        description="Get the latest messages from a Telegram channel.",
        args_schema=None,  # No arguments needed for this tool
    ),
)