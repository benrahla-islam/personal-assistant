import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from langchain.tools import tool
from config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Pydantic models for tool input validation
class ScheduleTaskInput(BaseModel):
    """Input schema for scheduling a task."""
    prompt: str = Field(
        description="The task/prompt to execute when the scheduled time arrives. Be specific about what you want the agent to do.",
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
    
    @validator('run_at')
    def validate_datetime(cls, v):
        """Validate the datetime format and ensure it's in the future."""
        try:
            if 'T' in v:
                dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            
            # Ensure timezone awareness
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            
            # Check if in future (with 1 minute buffer)
            min_future_time = datetime.now(timezone.utc) + timedelta(minutes=1)
            if dt <= min_future_time:
                raise ValueError("Scheduled time must be at least 1 minute in the future")
                
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
        scheduler = AsyncIOScheduler(timezone=timezone.utc)
        scheduler.start()
        logger.info("Task scheduler initialized and started")
    return scheduler

async def run_scheduled_task(prompt: str, task_id: str = None) -> None:
    """
    Run the scheduled task with proper error handling.
    
    Args:
        prompt: The prompt to execute
        task_id: Optional task identifier for logging
    """
    try:
        logger.info(f"Executing scheduled task{f' ({task_id})' if task_id else ''}: {prompt[:50]}...")
        
        # Avoid circular import by importing here
        from agent.main import agent_executor
        
        # Use the modern invoke method in a thread to avoid blocking the scheduler
        # The agent can call tools during execution - this runs the full workflow
        result = await asyncio.to_thread(
            agent_executor.invoke, {"input": prompt}
        )
        
        output = result.get("output", "No output received")
        logger.info(f"Scheduled task completed successfully{f' ({task_id})' if task_id else ''}")
        logger.debug(f"Task output: {output[:200]}...")
        
    except Exception as e:
        logger.error(f"Scheduled task failed{f' ({task_id})' if task_id else ''}: {e}", exc_info=True)

@tool(args_schema=ScheduleTaskInput)
def schedule_task(prompt: str, run_at: str, task_name: str = "Unnamed Task") -> str:
    """
    Schedule a task to run at a specific time.
    
    This tool will validate the input format and ensure the scheduled time is in the future.
    The scheduled task can call other tools like telegram scraper, other scheduling tasks, etc.
    
    Args:
        prompt: The task/prompt to execute when the scheduled time arrives
        run_at: When to run the task (YYYY-MM-DD HH:MM:SS or ISO format)
        task_name: Optional name for the task (for identification and logging)
        
    Returns:
        Success message with task ID or error message
    """
    try:
        # Parse the datetime string (validation already done by Pydantic)
        try:
            if 'T' in run_at:
                run_datetime = datetime.fromisoformat(run_at.replace('Z', '+00:00'))
            else:
                run_datetime = datetime.strptime(run_at, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            return f"Error: Invalid datetime format '{run_at}'. Use 'YYYY-MM-DD HH:MM:SS' or ISO format."
        
        # Ensure timezone awareness (default to UTC if none provided)
        if run_datetime.tzinfo is None:
            run_datetime = run_datetime.replace(tzinfo=timezone.utc)
            logger.warning(f"No timezone specified for task '{task_name}', assuming UTC")
        
        # Create the scheduler and add the job
        sched = get_scheduler()
        trigger = DateTrigger(run_date=run_datetime)
        
        job = sched.add_job(
            run_scheduled_task,
            trigger,
            args=[prompt, task_name],
            id=f"task_{int(run_datetime.timestamp())}_{hash(task_name) % 10000}",
            name=task_name,
            replace_existing=False
        )
        
        logger.info(f"Task '{task_name}' scheduled for {run_datetime.isoformat()}")
        return f"✅ Task '{task_name}' scheduled successfully for {run_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')} (Job ID: {job.id})"
        
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
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z') if job.next_run_time else "Unknown"
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
