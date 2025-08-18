import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from langchain.tools import tool
from config import get_logger
from telegram import Bot # general telegram bot API, not related to my specific bot logic


# Initialize logger
logger = get_logger(__name__)

# Pydantic models for tool input validation
class ScheduleTaskInput(BaseModel):
    """Input schema for scheduling a task."""
    prompt: str = Field(
        description="The task/prompt to be sent back to you when the scheduled time arrives. Be specific about what you want the agent to do. You will read this message and decide what to do next. write a comprehensive plan for the task.   ",
        min_length=1,
        max_length=1000,
        example="Get latest news from Telegram channels and summarize"
    )
    run_at: str = Field(
        description="When to run the task. Use format: 'YYYY-MM-DD HH:MM:SS' or ISO format '2025-08-11T15:30:00'. Must be in the future.",
        pattern=r"^\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}.*$",
        example="2025-08-11 15:30:00"
    )
    task_name: str = Field(
        default="Unnamed Task",
        description="Optional name for the task (for identification and logging). Keep it short and descriptive.",
        max_length=100,
        example="Daily News Summary"
    )
    chat_id: str = Field(
        description="The chat ID where the bot will send messages.",
        min_length=1,
        example="123456789"
    )

    @validator('run_at')
    def validate_datetime(cls, v):
        """Validate the datetime format and ensure it's in the future."""
        try:
            if 'T' in v:
                dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            
            # If no timezone is specified, assume UTC+1 (Central European Time)
            if dt.tzinfo is None:
                utc_plus_1 = timezone(timedelta(hours=1))
                dt = dt.replace(tzinfo=utc_plus_1)
                logger.info(f"No timezone specified, assuming UTC+1: {dt}")
            
            # Check if in future (with 1 minute buffer)
            # Compare in the same timezone as the input
            now_in_same_tz = datetime.now(dt.tzinfo)
            min_future_time = now_in_same_tz + timedelta(minutes=1)
            if dt <= min_future_time:
                raise ValueError(f"Scheduled time must be at least 1 minute in the future. Current time in {dt.tzinfo}: {now_in_same_tz.strftime('%Y-%m-%d %H:%M:%S')}")
                
            return v
        except ValueError as e:
            if "Scheduled time must be" in str(e):
                raise e
            raise ValueError(f"Invalid datetime format. Use 'YYYY-MM-DD HH:MM:SS' or '2025-08-11T15:30:00': {e}")
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Ensure the prompt is meaningful."""
        if len(v.strip()) == 0:
            raise ValueError("Prompt cannot be empty or just whitespace")
        return v.strip()

class CancelTaskInput(BaseModel):
    """Input schema for canceling a scheduled task."""
    task_id: str = Field(
        description="The ID of the task to cancel. Get this from list_scheduled_tasks first to see available task IDs.",
        min_length=1,
        example="task_1691763000_1234"
    )
    
    @validator('task_id')
    def validate_task_id(cls, v):
        """Ensure task ID is not empty."""
        if len(v.strip()) == 0:
            raise ValueError("Task ID cannot be empty")
        return v.strip()

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None

def get_scheduler() -> AsyncIOScheduler:
    """Get or create the global scheduler instance."""
    global scheduler
    if scheduler is None:
        # Use UTC+1 as the default timezone for the scheduler
        utc_plus_1 = timezone(timedelta(hours=1))
        scheduler = AsyncIOScheduler(timezone=utc_plus_1)
        scheduler.start()
        logger.info("Task scheduler initialized and started with UTC+1 timezone")
    return scheduler

async def run_scheduled_task(prompt: str, chat_id: str, task_id: str = None) -> None:
    """
    Run the scheduled task with proper error handling.
    
    Args:
        prompt: The prompt to execute
        chat_id: The chat ID where to send the response
        task_id: Optional task identifier for logging
    """
    try:
        logger.info(f"Executing scheduled task{f' ({task_id})' if task_id else ''}: {prompt[:50]}...")
        
        # Avoid circular import by importing here
        from agent.main_agent.main import agent_executor
        
        # Get current time with UTC+1 timezone for context
        current_time = datetime.now(timezone(timedelta(hours=1)))
        
        # Create a properly formatted prompt with timezone context
        # This ensures the agent has the same context as when used interactively
        formatted_prompt = f"""Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC+1 (Central European Time). 
From chat_id: {chat_id}, scheduled task reminder: {prompt}

IMPORTANT: If you need to schedule any tasks, use the same timezone (UTC+1) for the scheduled time."""
        
        # Use the modern invoke method in a thread to avoid blocking the scheduler
        # The agent can call tools during execution - this runs the full workflow
        result = await asyncio.to_thread(
            agent_executor.invoke, {"input": formatted_prompt}
        )
        
        output = result.get("output", "No output received")
        bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        await bot.send_message(chat_id=chat_id, text=output)
        logger.info(f"Scheduled task completed successfully{f' ({task_id})' if task_id else ''}")
        logger.debug(f"Task output: {output[:200]}...")
        
    except Exception as e:
        logger.error(f"Scheduled task failed{f' ({task_id})' if task_id else ''}: {e}", exc_info=True)

@tool(args_schema=ScheduleTaskInput)
def schedule_task(prompt: str, run_at: str, chat_id: str, task_name: str = "Unnamed Task") -> str:
    """
    Schedule a reminder or task for the user at a specific future time.
    
    When the scheduled time arrives, YOU (Jeffry) will receive the prompt as a message and can respond to the user 
    or take actions using your tools. Think of this as setting a reminder that will ping you to do something later.
    
    Use this when users ask to:
    - "Remind me to..." 
    - "Schedule a task for..."
    - "Set up a reminder..."
    - "Tell me to do X at Y time"
    
    The prompt should be clear instructions for what you should do when the time comes.
    Always use UTC+1 timezone for the run_at time.
    
    Args:
        prompt: Clear instructions for what you should do when the scheduled time arrives (what to remind the user about or what action to take)
        run_at: When to run the task in format 'YYYY-MM-DD HH:MM:SS' (always use UTC+1 timezone)
        chat_id: The user's chat ID (you should know this from context)
        task_name: Short descriptive name for the task (optional, defaults to "Unnamed Task")
        
    Returns:
        Success message with task ID or error message
    """
    logger.info(f"Scheduling tool is being called.  Scheduling task '{task_name}' to run at {run_at}")
    try:
        # Parse the datetime string (validation already done by Pydantic)
        try:
            if 'T' in run_at:
                run_datetime = datetime.fromisoformat(run_at.replace('Z', '+00:00'))
            else:
                run_datetime = datetime.strptime(run_at, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            return f"Error: Invalid datetime format '{run_at}'. Use 'YYYY-MM-DD HH:MM:SS' or ISO format."
        
        # If no timezone is specified, assume UTC+1 (Central European Time)
        if run_datetime.tzinfo is None:
            utc_plus_1 = timezone(timedelta(hours=1))
            run_datetime = run_datetime.replace(tzinfo=utc_plus_1)
            logger.info(f"No timezone specified for task '{task_name}', assuming UTC+1: {run_datetime}")
        else:
            logger.info(f"Using specified timezone for task '{task_name}': {run_datetime}")
        
        # Create the scheduler and add the job
        sched = get_scheduler()
        trigger = DateTrigger(run_date=run_datetime)
        
        job = sched.add_job(
            run_scheduled_task,
            trigger,
            args=[prompt, chat_id, task_name],
            id=f"task_{int(run_datetime.timestamp())}_{hash(task_name) % 10000}",
            name=task_name,
            replace_existing=False
        )
        
        logger.info(f"Task '{task_name}' scheduled for {run_datetime.isoformat()}")
        
        # Format the time display with timezone info
        time_display = run_datetime.strftime('%Y-%m-%d %H:%M:%S')
        if run_datetime.tzinfo:
            tz_name = "UTC+1" if run_datetime.utcoffset() == timedelta(hours=1) else str(run_datetime.tzinfo)
            time_display += f" {tz_name}"
        
        return f"✅ Task '{task_name}' scheduled successfully for {time_display} (Job ID: {job.id})"
        
    except Exception as e:
        error_msg = f"Failed to schedule task '{task_name}': {e}"
        logger.error(error_msg, exc_info=True)
        return f"❌ {error_msg}"

@tool
def list_scheduled_tasks() -> str:
    """
    List all currently scheduled tasks.
    
    This tool shows all pending scheduled tasks with their IDs, names, and next run times.
    Use this to see what tasks are currently scheduled and get their IDs for cancellation.
    
    Returns:
        Formatted list of scheduled tasks with their details
    """
    try:
        sched = get_scheduler()
        jobs = sched.get_jobs()
        
        if not jobs:
            return "📋 No tasks currently scheduled."
        
        task_list = ["📋 Scheduled Tasks:\n"]
        for job in jobs:
            if job.next_run_time:
                time_display = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
                if job.next_run_time.tzinfo:
                    tz_name = "UTC+1" if job.next_run_time.utcoffset() == timedelta(hours=1) else str(job.next_run_time.tzinfo)
                    time_display += f" {tz_name}"
                next_run = time_display
            else:
                next_run = "Unknown"
            task_list.append(f"• {job.name} (ID: {job.id})")
            task_list.append(f"  Next run: {next_run}")
            task_list.append("")
        
        return "\n".join(task_list)
        
    except Exception as e:
        error_msg = f"Failed to list scheduled tasks: {e}"
        logger.error(error_msg, exc_info=True)
        return f"❌ {error_msg}"

@tool(args_schema=CancelTaskInput)
def cancel_scheduled_task(task_id: str) -> str:
    """
    Cancel a scheduled task by its ID.
    
    Use list_scheduled_tasks first to see available task IDs.
    
    Args:
        task_id: The ID of the task to cancel
        
    Returns:
        Success or error message
    """
    try:
        sched = get_scheduler()
        sched.remove_job(task_id)
        logger.info(f"Cancelled scheduled task: {task_id}")
        return f"✅ Task '{task_id}' cancelled successfully."
        
    except Exception as e:
        error_msg = f"Failed to cancel task '{task_id}': {e}"
        logger.error(error_msg, exc_info=True)
        return f"❌ {error_msg}"
