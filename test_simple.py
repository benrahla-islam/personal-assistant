#!/usr/bin/env python3

from agent.specialized_agents.blueprint import Agent, create_agent_tool
from agent.specialized_agents.planner_agent import create_planner_agent, create_planner_tool

# Test simple Agent class
agent = Agent(tools=[], system_prompt='You are a test agent')
print(f'✅ Agent created: {type(agent).__name__}')

# Test planner
planner = create_planner_agent()
print(f'✅ Planner created: {type(planner).__name__} with {len(planner.tools)} tools')

# Test tool creation
tool = create_planner_tool()
print(f'✅ Tool created: {tool.name}')

print('✅ Simplified structure works!')
print(f'📏 Blueprint file: {len(open("agent/specialized_agents/blueprint.py").read())} chars')
print(f'📏 Planner file: {len(open("agent/specialized_agents/planner_agent.py").read())} chars')
