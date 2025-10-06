"""
Planner Agent - Task management and productivity specialist.

Handles: task organization, project planning, scheduling, habits, productivity optimization.
Integrates: Todoist API, local database, scheduling system.
"""

from .blueprint import Agent, create_agent_tool
from ..tools.planner_tools.todoist_tool import (
    todoist_add_tasks_tool,
    todoist_delete_task_tool, 
    todoist_update_task_tool,
    todoist_get_tasks_by_date_tool
)
from ..tools.task_scheduler import schedule_task, list_scheduled_tasks, cancel_scheduled_task
from ..tools.planner_tools.database_tools import get_database_tools

# Comprehensive tools for planning and productivity management
PLANNING_TOOLS = [
    # Todoist integration tools
    todoist_add_tasks_tool(),
    todoist_delete_task_tool(),
    todoist_update_task_tool(),
    todoist_get_tasks_by_date_tool(),
    
    # Scheduling and reminder tools
    schedule_task,
    list_scheduled_tasks,
    cancel_scheduled_task,
] + get_database_tools()  # Include all database tools for habits, tasks, schedules, and productivity tracking

# Concise prompt for planning agent
PLANNING_PROMPT = """You are a planning and task management assistant. Help users with:
- Creating and managing tasks in Todoist
- Breaking down projects into actionable steps
- Setting up schedules and reminders
- Building habits and tracking progress
- Organizing workflows and priorities

Be practical and actionable. Provide clear next steps."""

# Create planning agent
def create_planner_agent(shared_llm=None):
    return Agent(tools=PLANNING_TOOLS, system_prompt=PLANNING_PROMPT, shared_llm=shared_llm)

# Create planning tool with concise description
def create_planner_tool(shared_llm=None):
    return create_agent_tool(
        tools=PLANNING_TOOLS,
        system_prompt=PLANNING_PROMPT,
        tool_name="planner_agent",
        tool_description="Planning and task management specialist. Use for: task organization, project planning, scheduling, habit tracking, productivity optimization, goal setting. Has Todoist integration, scheduling tools, and habit/productivity database. Call when users need help organizing tasks, planning projects, building habits, or managing time.",
        shared_llm=shared_llm
    )

