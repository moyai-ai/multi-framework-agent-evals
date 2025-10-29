"""
Tool implementations for the Weather Agent System.

This module defines the function tools that the weather agent can use
to retrieve weather information.
"""

from typing import Optional
from agents import function_tool, RunContextWrapper
from .context import WeatherAgentContext
from .weather_service import get_weather, WeatherResponse


@function_tool(
    name_override="get_weather",
    description_override="Get current weather information for a specified city"
)
async def get_weather_tool(
    context: RunContextWrapper[WeatherAgentContext],
    city: str
) -> str:
    """
    Get the current weather for a city.

    Args:
        context: The current conversation context
        city: The name of the city to get weather for

    Returns:
        str: Weather information including temperature, conditions, and recommendations
    """
    print(f"get_weather tool called with city: {city}")

    try:
        # Fetch weather data
        weather_data: WeatherResponse = await get_weather(city)

        # Update context
        context.context.current_location = city
        context.context.last_temperature = weather_data.temperature
        context.context.last_conditions = weather_data.conditions
        context.context.last_recommendation = weather_data.recommendation
        context.context.conversation_stage = "weather_retrieved"

        # Format response
        response = f"""Weather in {weather_data.city}:
Temperature: {weather_data.temperature}
Conditions: {weather_data.conditions}
Recommendation: {weather_data.recommendation}"""

        return response

    except ValueError as e:
        return f"Sorry, I couldn't retrieve weather data for {city}. Please check the city name and try again."
    except Exception as e:
        return f"An error occurred while fetching weather data: {str(e)}"


@function_tool(
    name_override="compare_weather",
    description_override="Compare weather between two cities"
)
async def compare_weather_tool(
    context: RunContextWrapper[WeatherAgentContext],
    city1: str,
    city2: str
) -> str:
    """
    Compare weather between two cities.

    Args:
        context: The current conversation context
        city1: First city name
        city2: Second city name

    Returns:
        str: Comparison of weather between the two cities
    """
    print(f"compare_weather tool called with cities: {city1}, {city2}")

    try:
        # Fetch weather for both cities
        weather1: WeatherResponse = await get_weather(city1)
        weather2: WeatherResponse = await get_weather(city2)

        # Update context with the last queried location
        context.context.last_location = context.context.current_location
        context.context.current_location = f"{city1}, {city2}"
        context.context.conversation_stage = "weather_compared"

        # Format comparison response
        response = f"""Weather Comparison:

{weather1.city}:
- Temperature: {weather1.temperature}
- Conditions: {weather1.conditions}

{weather2.city}:
- Temperature: {weather2.temperature}
- Conditions: {weather2.conditions}

Recommendations:
- {weather1.city}: {weather1.recommendation}
- {weather2.city}: {weather2.recommendation}"""

        return response

    except ValueError as e:
        return f"Sorry, I couldn't retrieve weather data for one or both cities. Please check the city names and try again."
    except Exception as e:
        return f"An error occurred while comparing weather data: {str(e)}"
