"""
Custom output parser for ReAct agent that properly handles JSON tool inputs.
"""
import json
import re
from typing import Union, Any, Dict
from langchain.agents.agent import AgentAction, AgentFinish
from langchain.agents.react.output_parser import ReActOutputParser
from langchain.schema import OutputParserException
from config import get_logger

logger = get_logger(__name__)

class JSONCapableReActOutputParser(ReActOutputParser):
    """
    Custom ReAct output parser that properly parses JSON in Action Input.
    
    This fixes the issue where JSON strings are wrapped as single parameter values
    instead of being parsed into proper JSON objects.
    """
    
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse the output from the agent."""
        logger.debug(f"Parsing agent output: {text[:200]}...")
        
        # Check if this is a final answer
        if "Final Answer:" in text:
            final_answer = text.split("Final Answer:")[-1].strip()
            logger.debug(f"Found final answer: {final_answer[:100]}...")
            return AgentFinish({"output": final_answer}, text)
        
        # Look for Action and Action Input patterns
        action_match = re.search(r"Action:\s*(.+)", text)
        action_input_match = re.search(r"Action Input:\s*(.+?)(?=\n|$)", text, re.DOTALL)
        
        if not action_match:
            logger.warning("No action found in agent output")
            raise OutputParserException(f"Could not parse LLM output: `{text}`")
        
        action = action_match.group(1).strip()
        
        if not action_input_match:
            logger.warning("No action input found in agent output")
            raise OutputParserException(f"Could not parse LLM output: `{text}`")
        
        action_input_raw = action_input_match.group(1).strip()
        logger.debug(f"Raw action input: {action_input_raw}")
        
        # Try to parse as JSON first
        action_input = self._parse_action_input(action_input_raw)
        
        logger.info(f"Parsed action: {action} with input type: {type(action_input)}")
        if isinstance(action_input, dict):
            logger.debug(f"Action input keys: {list(action_input.keys())}")
        
        return AgentAction(tool=action, tool_input=action_input, log=text)
    
    def _parse_action_input(self, raw_input: str) -> Any:
        """
        Parse the action input, trying JSON first, then fallback to string.
        
        Args:
            raw_input: The raw action input string
            
        Returns:
            Parsed input (dict if valid JSON, string otherwise)
        """
        # Remove any surrounding quotes if present
        cleaned_input = raw_input.strip().strip('"').strip("'")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(cleaned_input)
            logger.debug(f"Successfully parsed JSON: {parsed}")
            return parsed
        except json.JSONDecodeError as e:
            logger.debug(f"JSON parsing failed: {e}, treating as string")
            
        # If JSON parsing fails, check if it looks like it should be JSON
        if cleaned_input.startswith('{') and cleaned_input.endswith('}'):
            logger.warning(f"Input looks like JSON but failed to parse: {cleaned_input[:100]}...")
            
            # Try to fix common JSON issues
            try:
                # Fix single quotes to double quotes
                fixed_input = cleaned_input.replace("'", '"')
                parsed = json.loads(fixed_input)
                logger.debug(f"Fixed and parsed JSON: {parsed}")
                return parsed
            except json.JSONDecodeError:
                logger.warning("Could not fix JSON, treating as string")
        
        # Return as string if not valid JSON
        logger.debug(f"Returning as string: {cleaned_input}")
        return cleaned_input
