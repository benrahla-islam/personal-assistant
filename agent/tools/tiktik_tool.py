"""
Tool for interacting with TikTik app to send daily tasks to the phone
"""

from langchain.tools import Tool


def tiktik_tool() -> Tool:
    async def send_task_to_tiktik(tasks: str) -> str:
        # Logic to send task list to the phone app
        # TODO: implement logic with api access
        return f"Task list sent to TikTik: {tasks}"

    return Tool(
        name="tiktik_tool",
        description="Tool for interacting with TikTik app to send daily tasks to the phone, not implemented yet, under construction",
        func=send_task_to_tiktik
    )
