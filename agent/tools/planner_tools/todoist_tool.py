"""
Tools for interacting with Todoist app for task management
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from langchain.tools import Tool
from dotenv import load_dotenv
load_dotenv()

from todoist_api_python.api import TodoistAPI


def _get_todoist_api() -> TodoistAPI:
    """Initialize and return Todoist API client"""
    api_token = os.getenv("TODOIST_API_TOKEN")
    if not api_token:
        raise ValueError("TODOIST_API_TOKEN environment variable not set. Please set your Todoist API token.")
    return TodoistAPI(api_token)


def todoist_add_tasks_tool() -> Tool:
    """Tool for adding multiple tasks to Todoist"""
    def add_multiple_tasks(tasks_input: str) -> str:
        """
        Add multiple tasks to Todoist
        
        Args:
            tasks_input: JSON string containing list of tasks or plain text tasks separated by newlines
                        Each task can be a string or dict with fields: content, description, due_date, priority, project_id
        
        Returns:
            Success/failure message with details
        """
        try:
            api = _get_todoist_api()
            
            # Parse tasks input
            task_list = []
            try:
                # Try to parse as JSON first
                parsed_tasks = json.loads(tasks_input)
                if isinstance(parsed_tasks, list):
                    task_list = parsed_tasks
                elif isinstance(parsed_tasks, str):
                    task_list = [parsed_tasks]
                else:
                    task_list = [str(parsed_tasks)]
            except json.JSONDecodeError:
                # If not JSON, treat as newline-separated tasks
                task_list = [task.strip() for task in tasks_input.split('\n') if task.strip()]
            
            if not task_list:
                return "No tasks provided to add to Todoist."
            
            # Add tasks to Todoist
            added_tasks = []
            failed_tasks = []
            
            for task in task_list:
                try:
                    if isinstance(task, dict):
                        # Task with detailed information
                        content = task.get('content', task.get('title', str(task)))
                        description = task.get('description', '')
                        due_string = task.get('due_date', task.get('due_string', None))
                        priority = task.get('priority', 1)
                        project_id = task.get('project_id', None)
                        labels = task.get('labels', [])
                        
                        task_obj = api.add_task(
                            content=content,
                            description=description,
                            due_string=due_string,
                            priority=priority,
                            project_id=project_id,
                            labels=labels
                        )
                    else:
                        # Simple string task
                        task_obj = api.add_task(content=str(task))
                    
                    added_tasks.append(task_obj.content)
                    
                except Exception as e:
                    failed_tasks.append(f"{task}: {str(e)}")
            
            # Prepare response message
            result_parts = []
            if added_tasks:
                result_parts.append(f"Successfully added {len(added_tasks)} task(s) to Todoist:")
                for task in added_tasks:
                    result_parts.append(f"  ✓ {task}")
            
            if failed_tasks:
                result_parts.append(f"\nFailed to add {len(failed_tasks)} task(s):")
                for failed in failed_tasks:
                    result_parts.append(f"  ✗ {failed}")
            
            return "\n".join(result_parts)
            
        except Exception as e:
            return f"Error connecting to Todoist API: {str(e)}"

    return Tool(
        name="todoist_add_tasks",
        description="""Add multiple tasks to Todoist at once. 
        Input should be either:
        1. Plain text with tasks separated by newlines
        2. JSON string with list of tasks
        3. JSON string with task objects containing 'content', 'description', 'due_date', 'priority', 'project_id', 'labels' fields
        
        Example inputs:
        - "Buy groceries\nCall dentist\nFinish report"
        - '["Buy groceries", "Call dentist", "Finish report"]'
        - '[{"content": "Buy groceries", "due_date": "today", "priority": 2, "labels": ["shopping"]}]'
        """,
        func=add_multiple_tasks
    )


def todoist_delete_task_tool() -> Tool:
    """Tool for deleting a task from Todoist"""
    def delete_task(task_id: str) -> str:
        """
        Delete a task from Todoist
        
        Args:
            task_id: The ID of the task to delete
        
        Returns:
            Success/failure message
        """
        try:
            api = _get_todoist_api()
            
            # Get task details before deletion for confirmation
            try:
                task = api.get_task(task_id)
                task_content = task.content
            except Exception:
                return f"Task with ID {task_id} not found."
            
            # Delete the task
            success = api.delete_task(task_id)
            
            if success:
                return f"Successfully deleted task: '{task_content}' (ID: {task_id})"
            else:
                return f"Failed to delete task with ID: {task_id}"
                
        except Exception as e:
            return f"Error deleting task: {str(e)}"

    return Tool(
        name="todoist_delete_task",
        description="Delete a task from Todoist by providing the task ID",
        func=delete_task
    )


def todoist_update_task_tool() -> Tool:
    """Tool for updating an existing task in Todoist"""
    def update_task(update_data: str) -> str:
        """
        Update an existing task in Todoist
        
        Args:
            update_data: JSON string containing task_id and fields to update
                        Example: '{"task_id": "123", "content": "Updated task", "due_date": "tomorrow", "priority": 3}'
        
        Returns:
            Success/failure message with updated task details
        """
        try:
            api = _get_todoist_api()
            
            # Parse update data
            try:
                update_info = json.loads(update_data)
            except json.JSONDecodeError:
                return "Invalid JSON format. Please provide update data as JSON with task_id and fields to update."
            
            task_id = update_info.get('task_id')
            if not task_id:
                return "task_id is required in the update data."
            
            # Extract update fields
            update_fields = {}
            if 'content' in update_info:
                update_fields['content'] = update_info['content']
            if 'description' in update_info:
                update_fields['description'] = update_info['description']
            if 'due_date' in update_info or 'due_string' in update_info:
                update_fields['due_string'] = update_info.get('due_date', update_info.get('due_string'))
            if 'priority' in update_info:
                update_fields['priority'] = update_info['priority']
            if 'labels' in update_info:
                update_fields['labels'] = update_info['labels']
            
            if not update_fields:
                return "No valid update fields provided. Available fields: content, description, due_date, priority, labels"
            
            # Update the task
            success = api.update_task(task_id, **update_fields)
            
            if success:
                # Get updated task details
                try:
                    updated_task = api.get_task(task_id)
                    return f"Successfully updated task: '{updated_task.content}' (ID: {task_id})"
                except Exception:
                    return f"Task updated successfully (ID: {task_id})"
            else:
                return f"Failed to update task with ID: {task_id}"
                
        except Exception as e:
            return f"Error updating task: {str(e)}"

    return Tool(
        name="todoist_update_task",
        description="""Update an existing task in Todoist. 
        Input should be JSON with task_id and fields to update.
        Available fields: content, description, due_date, priority, labels
        
        Example: '{"task_id": "123456789", "content": "Updated task name", "due_date": "tomorrow", "priority": 3}'
        """,
        func=update_task
    )


def todoist_get_tasks_by_date_tool() -> Tool:
    """Tool for getting tasks for a specific date from Todoist"""
    def get_tasks_by_date(date_filter: str) -> str:
        """
        Get tasks for a specific date from Todoist
        
        Args:
            date_filter: Date string (YYYY-MM-DD) or natural language like "today", "tomorrow", "overdue"
        
        Returns:
            List of tasks for the specified date
        """
        try:
            api = _get_todoist_api()
            
            # Get all tasks from Todoist
            tasks_response = api.get_tasks()
            
            # Convert paginator to list if needed
            if hasattr(tasks_response, '__iter__'):
                # The paginator returns a list of lists, so we need to flatten it
                paginated_result = list(tasks_response)
                if paginated_result and isinstance(paginated_result[0], list):
                    all_tasks = paginated_result[0]  # Get the actual tasks list
                else:
                    all_tasks = paginated_result
            else:
                all_tasks = tasks_response
            
            # Parse the date filter to determine what we're looking for
            target_date = None
            is_overdue = False
            
            if date_filter.lower() == 'today':
                target_date = date.today()
            elif date_filter.lower() == 'tomorrow':
                target_date = date.today() + timedelta(days=1)
            elif date_filter.lower() == 'overdue':
                is_overdue = True
            else:
                # Try to parse as YYYY-MM-DD format
                try:
                    target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                except ValueError:
                    # If not a valid date format, return all tasks with a note
                    filtered_tasks = all_tasks
                    result_parts = [f"Tasks (showing all - could not parse date filter '{date_filter}'):"]
                    
                    if not filtered_tasks:
                        return f"No tasks found."
                    
                    for task in filtered_tasks[:10]:  # Limit to first 10 tasks
                        task_info = f"• {task.content}"
                        if task.due:
                            task_info += f" (Due: {task.due.string})"
                        if task.priority > 1:
                            priority_text = {2: "High", 3: "Higher", 4: "Highest"}.get(task.priority, f"Priority {task.priority}")
                            task_info += f" [{priority_text}]"
                        task_info += f" (ID: {task.id})"
                        result_parts.append(task_info)
                    
                    if len(filtered_tasks) > 10:
                        result_parts.append(f"... and {len(filtered_tasks) - 10} more tasks")
                    
                    return "\n".join(result_parts)
            
            # Filter tasks based on criteria
            filtered_tasks = []
            
            for task in all_tasks:
                if is_overdue:
                    # Check for overdue tasks
                    if task.due and task.due.date:
                        try:
                            # task.due.date is already a date object
                            task_date = task.due.date
                            if isinstance(task_date, str):
                                task_date = datetime.strptime(task_date, '%Y-%m-%d').date()
                            if task_date < date.today():
                                filtered_tasks.append(task)
                        except (ValueError, AttributeError):
                            continue
                elif target_date:
                    # Check for tasks due on specific date
                    if task.due and task.due.date:
                        try:
                            # task.due.date is already a date object
                            task_date = task.due.date
                            if isinstance(task_date, str):
                                task_date = datetime.strptime(task_date, '%Y-%m-%d').date()
                            if task_date == target_date:
                                filtered_tasks.append(task)
                        except (ValueError, AttributeError):
                            continue
                    elif date_filter.lower() == 'today' and not task.due:
                        # Include tasks without due date when asking for today's tasks
                        filtered_tasks.append(task)
            
            if not filtered_tasks:
                return f"No tasks found for date: {date_filter}"
            
            # Format tasks for display
            result_parts = [f"Tasks for {date_filter} ({len(filtered_tasks)} found):"]
            
            for task in filtered_tasks:
                task_info = f"• {task.content}"
                
                # Add due date if available
                if task.due:
                    task_info += f" (Due: {task.due.string})"
                
                # Add priority if not normal
                if task.priority > 1:
                    priority_text = {2: "High", 3: "Higher", 4: "Highest"}.get(task.priority, f"Priority {task.priority}")
                    task_info += f" [{priority_text}]"
                
                # Add labels if any
                if task.labels:
                    task_info += f" Labels: {', '.join(task.labels)}"
                
                # Add task ID for reference
                task_info += f" (ID: {task.id})"
                
                result_parts.append(task_info)
            
            return "\n".join(result_parts)
            
        except Exception as e:
            return f"Error retrieving tasks: {str(e)}"

    return Tool(
        name="todoist_get_tasks_by_date",
        description="""Get tasks for a specific date from Todoist.
        Input can be:
        - Specific date in YYYY-MM-DD format (e.g., "2025-08-27")
        - Natural language like "today", "tomorrow", "overdue"
        - Relative dates like "next week", "this weekend"
        
        Returns detailed list of tasks with due dates, priorities, and labels.
        """,
        func=get_tasks_by_date
    )
