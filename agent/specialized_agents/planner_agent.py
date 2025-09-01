"""
Planner agent - simple configuration for task management.
"""

from .blueprint import Agent, create_agent_tool
from ..tools.planner_tools.todoist_tool import (
    todoist_add_tasks_tool,
    todoist_delete_task_tool, 
    todoist_update_task_tool,
    todoist_get_tasks_by_date_tool
)
from ..tools.task_scheduler import schedule_task, list_scheduled_tasks, cancel_scheduled_task

# Tools for planning
PLANNING_TOOLS = [
    todoist_add_tasks_tool(),
    todoist_delete_task_tool(),
    todoist_update_task_tool(),
    todoist_get_tasks_by_date_tool(),
    schedule_task,
    list_scheduled_tasks,
    cancel_scheduled_task
]

# Prompt for planning
PLANNING_PROMPT = """You are a planning and task management assistant. Help users with:
- Creating and managing tasks in Todoist
- Scheduling reminders
- Breaking down projects into tasks
- Time management and prioritization"""

# Create planning agent
def create_planner_agent():
    return Agent(tools=PLANNING_TOOLS, system_prompt=PLANNING_PROMPT)

# Create planning tool
def create_planner_tool():
    return create_agent_tool(
        tools=PLANNING_TOOLS,
        system_prompt=PLANNING_PROMPT,
        tool_name="planner_agent",
        tool_description="Planning and task management agent"
    )

# Backwards compatibility
def create_react_planner_tool():
    return create_planner_tool()

def create_react_agent_tool():
    return create_planner_tool()

async def create_react_agent_tool_async():
    return create_agent_tool(
        tools=PLANNING_TOOLS,
        system_prompt=PLANNING_PROMPT,
        tool_name="planner_agent",
        tool_description="Planning and task management agent",
        async_mode=True
    )