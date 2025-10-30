"""Google ADK agent definitions for Hacker News analytics."""

import logging
from typing import Dict, Optional, List, Any

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

from .prompts import (
    HACKER_NEWS_AGENT_PROMPT,
    SEARCH_AGENT_PROMPT,
    TRENDING_AGENT_PROMPT,
    USER_AGENT_PROMPT,
    COMMENT_AGENT_PROMPT
)
from .tools import HN_TOOLS

logger = logging.getLogger(__name__)


def _process_hn_response(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse:
    """Post-process LLM response to ensure valid JSON output.

    Args:
        callback_context: Callback context from the agent
        llm_response: Raw LLM response

    Returns:
        Processed LLM response
    """
    # Log the response for debugging
    if llm_response.text:
        logger.debug(f"HN Agent response: {llm_response.text[:500]}...")

    # Could add additional processing here if needed
    # For example, validating JSON structure or adding metadata

    return llm_response


# Main Hacker News agent
hacker_news_agent = Agent(
    model='gemini-2.0-flash',
    name='hacker_news_agent',
    description='Main agent for Hacker News search and analytics',
    instruction=HACKER_NEWS_AGENT_PROMPT,
    tools=HN_TOOLS,
    after_model_callback=_process_hn_response,
)

# Specialized search agent
search_agent = Agent(
    model='gemini-2.0-flash',
    name='search_agent',
    description='Specialized agent for searching Hacker News content',
    instruction=SEARCH_AGENT_PROMPT,
    tools=[HN_TOOLS[0]],  # Just the search tool
)

# Trending analysis agent
trending_agent = Agent(
    model='gemini-2.0-flash',
    name='trending_agent',
    description='Agent for analyzing trending stories on Hacker News',
    instruction=TRENDING_AGENT_PROMPT,
    tools=[HN_TOOLS[1]],  # Just the trending tool
)

# User analytics agent
user_agent = Agent(
    model='gemini-2.0-flash',
    name='user_agent',
    description='Agent for analyzing Hacker News user profiles',
    instruction=USER_AGENT_PROMPT,
    tools=[HN_TOOLS[2]],  # Just the user tool
)

# Comment analysis agent
comment_agent = Agent(
    model='gemini-2.0-flash',
    name='comment_agent',
    description='Agent for analyzing Hacker News comment threads',
    instruction=COMMENT_AGENT_PROMPT,
    tools=[HN_TOOLS[3]],  # Just the comments tool
)

# Sequential agent for complex multi-step analysis
multi_agent = SequentialAgent(
    name='multi_analysis_agent',
    description='Sequential agent for complex HN analysis tasks',
    sub_agents=[trending_agent, search_agent, comment_agent]
)

# Agent registry
AGENTS: Dict[str, Agent] = {
    'hacker_news_agent': hacker_news_agent,
    'search_agent': search_agent,
    'trending_agent': trending_agent,
    'user_agent': user_agent,
    'comment_agent': comment_agent,
    'multi_analysis_agent': multi_agent,
}


def get_agent_by_name(name: str) -> Optional[Agent]:
    """Get an agent by exact or partial name match.

    Args:
        name: Agent name or partial name

    Returns:
        Matching agent or None
    """
    # Try exact match first
    if name in AGENTS:
        return AGENTS[name]

    # Try partial match
    name_lower = name.lower()
    for agent_name, agent in AGENTS.items():
        if name_lower in agent_name.lower():
            logger.info(f"Partial match: '{name}' matched to '{agent_name}'")
            return agent

    logger.warning(f"No agent found for name: {name}")
    return None


def get_initial_agent() -> Agent:
    """Get the default/initial agent for the system.

    Returns:
        The main hacker_news_agent
    """
    return hacker_news_agent


def list_agents() -> List[Dict[str, str]]:
    """List all available agents with their descriptions.

    Returns:
        List of agent information dictionaries
    """
    return [
        {
            "name": name,
            "description": agent.description or "No description",
            "model": getattr(agent, 'model', 'N/A'),
            "tools": len(getattr(agent, 'tools', [])) if hasattr(agent, 'tools') else 0
        }
        for name, agent in AGENTS.items()
    ]


def get_agent_for_query(query: str) -> Agent:
    """Select the best agent based on the query type.

    Args:
        query: User query string

    Returns:
        Most appropriate agent for the query
    """
    query_lower = query.lower()

    # Route to specialized agents based on keywords
    if any(word in query_lower for word in ['trend', 'trending', 'popular', 'hot', 'top']):
        logger.info("Routing to trending_agent")
        return trending_agent
    elif any(word in query_lower for word in ['search', 'find', 'look for']):
        logger.info("Routing to search_agent")
        return search_agent
    elif any(word in query_lower for word in ['user', 'profile', 'karma', 'who is']):
        logger.info("Routing to user_agent")
        return user_agent
    elif any(word in query_lower for word in ['comment', 'discussion', 'thread', 'sentiment']):
        logger.info("Routing to comment_agent")
        return comment_agent

    # Default to main agent
    logger.info("Using default hacker_news_agent")
    return hacker_news_agent