"""
Agent definitions for the Weather Agent System.

This module defines the weather assistant agent that can provide
weather information and recommendations.
"""

from typing import Dict, Optional
from agents import Agent
from .context import WeatherAgentContext
from .tools import get_weather_tool, compare_weather_tool


# Weather Agent - Main agent that provides weather information
weather_agent = Agent[WeatherAgentContext](
    name="Weather Agent",
    model="gpt-4o",
    instructions="""
You are a friendly weather assistant that helps users get current weather information.

Your capabilities:
- Provide current weather information for cities around the world
- Offer contextual recommendations based on weather conditions
- Compare weather between different locations
- Suggest appropriate clothing and activities based on conditions

Your workflow:
1. Understand what location the user is asking about
2. If the location is ambiguous (e.g., "Paris" could be Paris, France or Paris, Texas), ask for clarification
3. Use the get_weather tool to fetch current weather data
4. Provide the information in a friendly, conversational way
5. Offer helpful recommendations based on the conditions

Available tools:
- get_weather: Get current weather for a specific city
- compare_weather: Compare weather between two cities

Important guidelines:
- Always be friendly and helpful
- Provide practical recommendations (umbrella, jacket, etc.)
- If you can't find weather data, politely ask the user to verify the city name
- When discussing temperatures, include both Fahrenheit and Celsius when possible
- Consider the context - if someone asks "should I bring an umbrella?", check for rain conditions
- For activity suggestions, consider the weather conditions holistically

Remember: Your goal is to help users make informed decisions about their day based on weather conditions.
""",
    tools=[get_weather_tool, compare_weather_tool]
)


# Agent registry for easy lookup
AGENTS: Dict[str, Agent[WeatherAgentContext]] = {
    "weather": weather_agent
}


def get_agent_by_name(name: str) -> Optional[Agent[WeatherAgentContext]]:
    """
    Get an agent by name.

    Args:
        name: Agent name (can be partial match)

    Returns:
        Agent if found, None otherwise
    """
    name_lower = name.lower()

    # Try exact match first
    if name_lower in AGENTS:
        return AGENTS[name_lower]

    # Try partial match
    for key, agent in AGENTS.items():
        if name_lower in key or name_lower in agent.name.lower():
            return agent

    return None


def get_initial_agent() -> Agent[WeatherAgentContext]:
    """
    Get the initial agent for new conversations.

    Returns:
        The Weather Agent
    """
    return weather_agent


def list_agents() -> list:
    """
    Get a list of all available agents with their descriptions.

    Returns:
        List of agent information dictionaries
    """
    return [
        {
            "name": agent.name,
            "key": key,
            "tools": [tool.name if hasattr(tool, 'name') else str(tool) for tool in (agent.tools or [])],
        }
        for key, agent in AGENTS.items()
    ]
