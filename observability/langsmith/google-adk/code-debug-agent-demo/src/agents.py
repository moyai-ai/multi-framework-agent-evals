"""Code Debug Agent implementation using Google ADK.

Note: LangSmith tracing decorators are NOT applied directly to callback functions
because they interfere with Google ADK's function signature parsing. Instead,
tracing is handled at the runner level in src/runner.py and src/traced_runner.py.
"""

import logging
import os
from typing import Dict, Optional, List, Any
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from src.tools import DEBUG_TOOLS
from src.prompts import DEBUG_AGENT_PROMPT

logger = logging.getLogger(__name__)

# Get model from environment variable or use default
# gemini-2.0-flash is the stable version with better rate limits than gemini-2.0-flash-exp
DEFAULT_MODEL = "gemini-2.0-flash"
MODEL = os.getenv("GOOGLE_MODEL", DEFAULT_MODEL)


def _format_debug_response(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse:
    """Format the debug agent's response for better readability.

    This callback processes the LLM response to ensure consistent formatting
    and adds helpful metadata when Stack Exchange results are included.

    Args:
        callback_context: Context from the agent execution
        llm_response: The raw LLM response

    Returns:
        Formatted LLM response
    """
    try:
        # Log the response for debugging
        # LlmResponse might have different attributes - let's check what's available
        if hasattr(llm_response, 'text') and llm_response.text:
            logger.debug(f"Debug agent response: {llm_response.text[:200]}...")
        elif hasattr(llm_response, 'content'):
            # Log content if available
            logger.debug(f"Debug agent response content available")

        # Could add additional formatting here if needed
        # For example, adding markdown formatting or extracting links

    except Exception as e:
        logger.error(f"Error formatting response: {e}")

    return llm_response


# Main Debug Agent
debug_agent = Agent(
    model=MODEL,
    name='debug_agent',
    instruction=DEBUG_AGENT_PROMPT,
    tools=DEBUG_TOOLS,
    after_model_callback=_format_debug_response,
)


# Quick Error Lookup Agent (simpler, faster responses)
quick_debug_agent = Agent(
    model=MODEL,
    name='quick_debug_agent',
    instruction="""You are a quick debugging assistant. When given an error message, immediately search Stack Exchange for the most relevant solution and provide a concise fix.

Follow these steps:
1. Use search_stack_exchange_for_error to find solutions
2. Present the top solution concisely
3. Include the Stack Exchange link for reference

Keep responses brief and actionable.""",
    tools=[DEBUG_TOOLS[0], DEBUG_TOOLS[3]],  # Only error search and analysis tools
)


# Agent Registry
AGENTS: Dict[str, Agent] = {
    'debug_agent': debug_agent,
    'quick_debug_agent': quick_debug_agent,
}


def get_agent_by_name(name: str) -> Optional[Agent]:
    """Get an agent by exact or partial name match.

    Args:
        name: The agent name or partial name to search for

    Returns:
        The matching agent or None if not found
    """
    # Try exact match first
    if name in AGENTS:
        return AGENTS[name]

    # Try partial match (case-insensitive)
    name_lower = name.lower()
    for agent_name, agent in AGENTS.items():
        if name_lower in agent_name.lower():
            return agent

    return None


def get_initial_agent() -> Agent:
    """Get the default/initial agent for the application.

    Returns:
        The main debug agent
    """
    return debug_agent


def list_agents() -> List[Dict[str, Any]]:
    """List all available agents with their metadata.

    Returns:
        List of agent information dictionaries
    """
    agents_info = []
    for name, agent in AGENTS.items():
        # Handle both regular Agent and SequentialAgent
        if hasattr(agent, 'model'):
            # Regular Agent
            agent_info = {
                'name': name,
                'model': agent.model,
                'tools_count': len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0,
                'tools': [tool.name for tool in (agent.tools or [])] if hasattr(agent, 'tools') else [],
                'description': agent.instruction[:200] if hasattr(agent, 'instruction') and agent.instruction else 'No description',
            }
        else:
            # SequentialAgent or other agent types without model attribute
            agent_info = {
                'name': name,
                'model': 'Sequential (multiple models)',
                'tools_count': 0,  # Sequential agents don't directly have tools
                'tools': [],
                'description': f"Sequential agent with {len(agent.sub_agents) if hasattr(agent, 'sub_agents') else 0} sub-agents",
            }

            # Add sub-agent details if available
            if hasattr(agent, 'sub_agents') and agent.sub_agents:
                sub_agent_names = [sub.name if hasattr(sub, 'name') else 'unnamed' for sub in agent.sub_agents]
                agent_info['sub_agents'] = sub_agent_names

        agents_info.append(agent_info)

    return agents_info


# Optional: Create a sequential agent for complex debugging workflows
try:
    from google.adk.agents import SequentialAgent

    # Error Analyzer Agent (first step)
    error_analyzer = Agent(
        model=MODEL,
        name='error_analyzer',
        instruction="""Analyze the provided error message and identify:
1. Error type and category
2. Affected components/modules
3. Programming language and framework
4. Key search terms for finding solutions

Output a structured analysis that the next agent can use to search for solutions.""",
        tools=[],  # No tools needed, just analysis
    )

    # Solution Finder Agent (second step)
    solution_finder = Agent(
        model=MODEL,
        name='solution_finder',
        instruction="""Based on the error analysis, search Stack Exchange for the best solutions.
Use the search tools to find relevant fixes and present them clearly.""",
        tools=DEBUG_TOOLS,
    )

    # Sequential Debug Agent
    sequential_debug_agent = SequentialAgent(
        name='sequential_debug_agent',
        sub_agents=[error_analyzer, solution_finder],
    )

    # Add to registry
    AGENTS['sequential_debug_agent'] = sequential_debug_agent

except ImportError:
    logger.info("SequentialAgent not available, using single agents only")


# Export key components
__all__ = [
    'debug_agent',
    'quick_debug_agent',
    'get_agent_by_name',
    'get_initial_agent',
    'list_agents',
    'AGENTS',
]
