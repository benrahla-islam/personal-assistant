from telegram import Update
from telegram.ext import ContextTypes
import logging
from datetime import datetime, timezone, timedelta
# Set up colored logging
from config import setup_development_logging, get_logger

setup_development_logging()
logger = get_logger(__name__)

# Import agent with logging
try:
    logger.info("Importing agent module...")
    from agent.main_agent import agent_executor as agent
    logger.info(f"Agent imported successfully. Type: {type(agent)}")
    logger.info(f"Agent attributes: {[attr for attr in dir(agent) if not attr.startswith('_')]}")
except Exception as e:
    logger.error(f"Failed to import agent: {e}", exc_info=True)
    agent = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}!\n\n"
        f"I'm your personal assistant bot. Here's what I can do:\n"
        f"• Send me any message and I'll echo it back\n"
        f"• Use /help to see available commands\n"
        f"• Use /info to get information about yourself"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
Available commands:

/start - Start the bot and see welcome message
/help - Show this help message
/info - Get your user information
/echo <message> - Echo back your message
/caps <message> - Convert your message to CAPS

Just send me any text message and I'll echo it back to you!
    """
    await update.message.reply_text(help_text)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send user information when the command /info is issued."""
    user = update.effective_user
    chat = update.effective_chat
    
    info_text = f"""
Your Information:
• Name: {user.full_name}
• Username: @{user.username if user.username else 'Not set'}
• User ID: {user.id}
• Chat ID: {chat.id}
• Chat Type: {chat.type}
    """
    await update.message.reply_text(info_text)

async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message after /echo command."""
    message_text = ' '.join(context.args)
    if message_text:
        await update.message.reply_text(f"Echo: {message_text}")
    else:
        await update.message.reply_text("Please provide a message to echo. Usage: /echo <message>")

async def caps_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Convert message to uppercase after /caps command."""
    message_text = ' '.join(context.args)
    if message_text:
        await update.message.reply_text(message_text.upper())
    else:
        await update.message.reply_text("Please provide a message to convert. Usage: /caps <message>")

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process user message with the agent."""
    user_message = update.message.text
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    logger.info(f"Processing message from user {user_id}: '{user_message[:100]}...'")
    
    # Check if agent is available
    if agent is None:
        logger.error("Agent is not available - import failed")
        await update.message.reply_text(
            "Sorry, the AI agent is not available right now. Please try again later."
        )
        return
    
    try:
        # Send a "thinking" message to show the bot is processing
        thinking_message = await update.message.reply_text("🤔 Thinking...")
        logger.debug(f"Sent thinking message to user {user_id}")
        
        # Run the agent using the modern LangChain API
        agent_response = None
        try:
            logger.debug(f"Attempting agent.invoke() for user {user_id}")
            # Use the modern invoke method with proper input format for ReAct agents
            # Use UTC+1 timezone (Central European Time)
            utc_plus_1 = timezone(timedelta(hours=1))
            current_time = datetime.now(utc_plus_1)
            prompt = f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC+1 (Central European Time). From chat_id: {chat_id}, the user asked: {user_message}"
            agent_response = agent.invoke({
                "input": prompt
            })
            logger.debug(f"Got agent response: {type(agent_response)}")
            logger.info(f"Agent invoke completed for user {user_id}")
            
        except Exception as agent_error:
            # Handle specific OutputParserException
            if "Could not parse LLM output" in str(agent_error):
                logger.warning(f"LLM output parsing failed for user {user_id}, trying to extract message from error")
                error_text = str(agent_error)
                # Try to extract the actual LLM response from the error message
                if "`" in error_text:
                    start_idx = error_text.find("`") + 1
                    end_idx = error_text.rfind("`")
                    if start_idx > 0 and end_idx > start_idx:
                        extracted_response = error_text[start_idx:end_idx]
                        logger.debug(f"Extracted LLM response from error: {extracted_response[:100]}...")
                        # Use the extracted response as a fallback
                        response_text = extracted_response
                        logger.info(f"Using extracted response for user {user_id}")
                        # Skip to sending the response
                        logger.info(f"Agent response preview: '{response_text[:200]}...'")
                        # Continue with response processing...
                        original_length = len(response_text)
                        if len(response_text) > 4000:
                            response_text = response_text[:4000] + "... (message truncated)"
                            logger.warning(f"Response truncated from {original_length} to 4000 characters")
                        
                        # Edit the thinking message with the actual response
                        logger.debug(f"Sending extracted response to user {user_id}")
                        try:
                            await thinking_message.edit_text(response_text, parse_mode='Markdown')
                            logger.info(f"Successfully sent extracted response to user {user_id}")
                        except Exception as format_error:
                            logger.warning(f"Markdown formatting failed, sending as plain text: {format_error}")
                            await thinking_message.edit_text(response_text)
                            logger.info(f"Successfully sent plain text response to user {user_id}")
                        return
            
            logger.error(f"Agent call failed for user {user_id}: {agent_error}")
            raise agent_error
        
        # Log the type and structure of the agent response
        logger.debug(f"Agent response type: {type(agent_response)}")
        logger.debug(f"Agent response attributes: {dir(agent_response)}")
        
        # Extract and format the response text from the agent response
        response_text = None
        
        # Handle AgentFinish (final response)
        if hasattr(agent_response, 'return_values') and hasattr(agent_response, 'log'):
            logger.debug("Processing AgentFinish response")
            if isinstance(agent_response.return_values, dict) and 'output' in agent_response.return_values:
                response_text = agent_response.return_values['output']
                logger.debug(f"Extracted clean output from AgentFinish: {len(response_text)} chars")
            else:
                response_text = str(agent_response.return_values)
                logger.debug(f"Extracted return_values as string: {len(response_text)} chars")
        
        # Handle AgentAction (tool execution request)
        elif hasattr(agent_response, 'tool') and hasattr(agent_response, 'tool_input'):
            # logger.debug("Processing AgentAction response")
            # tool_name = agent_response.tool
            # tool_input = agent_response.tool_input
            
            # # Format different tool responses
            # if tool_name == 'schedule_task':
            #     if isinstance(tool_input, str):
            #         import json
            #         try:
            #             tool_data = json.loads(tool_input)
            #             task_name = tool_data.get('task_name', 'Scheduled Task')
            #             prompt = tool_data.get('prompt', 'Task reminder')
            #             run_at = tool_data.get('run_at', 'Unknown time')
            #             response_text = f"✅ **Task Scheduled Successfully!**\n\n" \
            #                         f"📝 **Task:** {task_name}\n" \
            #                         f"💬 **Reminder:** {prompt}\n" \
            #                         f"⏰ **Scheduled for:** {run_at}\n\n" \
            #                         f"I'll remind you when it's time!"
            #         except json.JSONDecodeError:
            #             response_text = f"⚙️ Scheduling task with: {tool_input}"
            #     else:
            #         response_text = f"⚙️ Scheduling task with: {tool_input}"
            
            # elif tool_name == 'telegram_scraper':
            #     response_text = f"🔍 **Searching Telegram channels...**\n\n" \
            #                 f"I'm looking for the information you requested. This may take a moment."
            
            # elif tool_name == 'telegram_conversation_sender':
            #     response_text = f"📤 **Sending message to Telegram...**\n\n" \
            #                 f"Your message is being sent."
            
            # else:
            #     # Generic tool execution message
            #     response_text = f"🛠️ **Executing {tool_name}...**\n\n" \
            #                 f"Working on your request with the following parameters:\n" \
            #                 f"```\n{tool_input}\n```"
            
            # logger.debug(f"Formatted AgentAction response: {len(response_text)} chars")
            response_text = agent_response
        
        # Fallback extraction methods
        elif isinstance(agent_response, dict) and 'output' in agent_response:
            response_text = str(agent_response['output'])
            logger.debug(f"Extracted response from ['output'] key: {len(response_text)} chars")
        elif hasattr(agent_response, 'content'):
            response_text = str(agent_response.content)
            logger.debug(f"Extracted response from .content attribute: {len(response_text)} chars")
        elif hasattr(agent_response, 'response'):
            response_text = str(agent_response.response)
            logger.debug(f"Extracted response from .response attribute: {len(response_text)} chars")
        elif hasattr(agent_response, 'text'):
            response_text = str(agent_response.text)
            logger.debug(f"Extracted response from .text attribute: {len(response_text)} chars")
        elif hasattr(agent_response, 'message'):
            response_text = str(agent_response.message)
            logger.debug(f"Extracted response from .message attribute: {len(response_text)} chars")
        else:
            response_text = str(agent_response)
            logger.debug(f"Extracted response from str() conversion: {len(response_text)} chars")
        
        # Log the first part of the response for debugging
        logger.info(f"Agent response preview: '{response_text[:200]}...'")
        
        # Limit response length to avoid Telegram's message limit
        original_length = len(response_text)
        if len(response_text) > 4000:
            response_text = response_text[:4000] + "... (message truncated)"
            logger.warning(f"Response truncated from {original_length} to 4000 characters")
        
        # Edit the thinking message with the actual response
        logger.debug(f"Sending final response to user {user_id}")
        try:
            # Try to send with Markdown formatting first
            await thinking_message.edit_text(response_text, parse_mode='Markdown')
            logger.info(f"Successfully sent formatted response to user {user_id}")
        except Exception as format_error:
            logger.warning(f"Markdown formatting failed, sending as plain text: {format_error}")
            # Fallback to plain text if Markdown fails
            await thinking_message.edit_text(response_text)
            logger.info(f"Successfully sent plain text response to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error processing message with agent for user {user_id}: {e}", exc_info=True)
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        
        try:
            await update.message.reply_text(
                "Sorry, I encountered an error while processing your message. "
                f"Error details: {str(e)[:200]}"
            )
            logger.info(f"Sent error message to user {user_id}")
        except Exception as reply_error:
            logger.error(f"Failed to send error message to user {user_id}: {reply_error}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("=" * 50)
    logger.error("TELEGRAM BOT ERROR HANDLER TRIGGERED")
    logger.error("=" * 50)
    
    # Log the error details
    if context.error:
        logger.error(f"Error type: {type(context.error)}")
        logger.error(f"Error message: {context.error}")
        logger.error(f"Error args: {getattr(context.error, 'args', 'No args')}")
        logger.error("Full traceback:", exc_info=context.error)
    
    # Log update details if available
    if update:
        logger.error(f"Update type: {type(update)}")
        if hasattr(update, 'effective_user') and update.effective_user:
            logger.error(f"User ID: {update.effective_user.id}")
            logger.error(f"Username: {update.effective_user.username}")
        if hasattr(update, 'effective_message') and update.effective_message:
            logger.error(f"Message text: {getattr(update.effective_message, 'text', 'No text')}")
    
    logger.error("=" * 50)