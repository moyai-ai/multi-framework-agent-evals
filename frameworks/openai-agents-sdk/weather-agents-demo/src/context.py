"""
Context management for the Weather Agent System.

This module defines the shared context model that maintains state
across conversation turns.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class WeatherAgentContext(BaseModel):
    """
    Shared context for weather agent.

    This context maintains weather information and user preferences
    throughout the conversation.
    """

    # Location tracking
    current_location: Optional[str] = Field(
        default=None,
        description="The current city/location being queried"
    )

    last_location: Optional[str] = Field(
        default=None,
        description="The previous location queried"
    )

    # Weather data cache
    last_temperature: Optional[str] = Field(
        default=None,
        description="Last retrieved temperature"
    )

    last_conditions: Optional[str] = Field(
        default=None,
        description="Last retrieved weather conditions"
    )

    last_recommendation: Optional[str] = Field(
        default=None,
        description="Last weather recommendation provided"
    )

    # Conversation tracking
    last_query: Optional[str] = Field(
        default=None,
        description="Last weather query made by user"
    )

    conversation_stage: Optional[str] = Field(
        default="initial",
        description="Current stage of the conversation"
    )


def create_initial_context() -> WeatherAgentContext:
    """
    Create an initial context for a new conversation.

    Returns:
        WeatherAgentContext: Initial context
    """
    return WeatherAgentContext(
        conversation_stage="initial"
    )


def create_test_context(**kwargs) -> WeatherAgentContext:
    """
    Create a context for testing with specific values.

    This is useful for test scenarios where you want to preset
    certain context values.

    Args:
        **kwargs: Any valid WeatherAgentContext fields

    Returns:
        WeatherAgentContext: Context with specified values
    """
    # Start with initial context
    context = create_initial_context()

    # Update with provided values
    for key, value in kwargs.items():
        if hasattr(context, key):
            setattr(context, key, value)

    return context


def update_context(
    context: WeatherAgentContext,
    updates: Dict[str, Any]
) -> WeatherAgentContext:
    """
    Update context with new values.

    Args:
        context: Current context
        updates: Dictionary of updates to apply

    Returns:
        WeatherAgentContext: Updated context
    """
    # Create a copy of the context
    context_dict = context.model_dump()

    # Apply updates
    context_dict.update(updates)

    # Return new context
    return WeatherAgentContext(**context_dict)


def context_diff(
    old_context: WeatherAgentContext,
    new_context: WeatherAgentContext
) -> Dict[str, Any]:
    """
    Get the differences between two contexts.

    This is useful for tracking what changed during an agent's execution.

    Args:
        old_context: Previous context state
        new_context: Current context state

    Returns:
        Dict[str, Any]: Dictionary of changed fields with new values
    """
    old_dict = old_context.model_dump()
    new_dict = new_context.model_dump()

    changes = {}
    for key, new_value in new_dict.items():
        old_value = old_dict.get(key)
        if old_value != new_value:
            changes[key] = new_value

    return changes
