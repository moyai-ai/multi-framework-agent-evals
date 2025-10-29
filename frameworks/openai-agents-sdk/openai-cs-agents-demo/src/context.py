"""
Context management for the Airline Customer Service Agent System.

This module defines the shared context model that maintains state
across agent handoffs and conversation turns.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import random
import string


class AirlineAgentContext(BaseModel):
    """
    Shared context for airline customer service agents.

    This context is passed between agents during handoffs and maintains
    important customer and flight information throughout the conversation.
    """

    # Customer information
    passenger_name: Optional[str] = Field(
        default=None,
        description="The name of the passenger"
    )

    account_number: Optional[str] = Field(
        default=None,
        description="Customer's airline account number"
    )

    # Flight information
    confirmation_number: Optional[str] = Field(
        default=None,
        description="Booking confirmation number"
    )

    flight_number: Optional[str] = Field(
        default=None,
        description="Flight number (e.g., 'UA456')"
    )

    seat_number: Optional[str] = Field(
        default=None,
        description="Current seat assignment"
    )

    # Additional context for tracking
    last_action: Optional[str] = Field(
        default=None,
        description="Last action performed by an agent"
    )

    conversation_stage: Optional[str] = Field(
        default="initial",
        description="Current stage of the conversation"
    )


def create_initial_context() -> AirlineAgentContext:
    """
    Create an initial context with a generated account number.

    This is used when starting a new conversation to provide
    a consistent customer identity.

    Returns:
        AirlineAgentContext: Initial context with generated account number
    """
    # Generate a random account number for demo purposes
    account_number = ''.join(random.choices(string.digits, k=12))

    return AirlineAgentContext(
        account_number=f"AC{account_number}",
        conversation_stage="initial"
    )


def create_test_context(**kwargs) -> AirlineAgentContext:
    """
    Create a context for testing with specific values.

    This is useful for test scenarios where you want to preset
    certain context values.

    Args:
        **kwargs: Any valid AirlineAgentContext fields

    Returns:
        AirlineAgentContext: Context with specified values
    """
    # Start with initial context
    context = create_initial_context()

    # Update with provided values
    for key, value in kwargs.items():
        if hasattr(context, key):
            setattr(context, key, value)

    return context


def update_context(
    context: AirlineAgentContext,
    updates: Dict[str, Any]
) -> AirlineAgentContext:
    """
    Update context with new values.

    Args:
        context: Current context
        updates: Dictionary of updates to apply

    Returns:
        AirlineAgentContext: Updated context
    """
    # Create a copy of the context
    context_dict = context.model_dump()

    # Apply updates
    context_dict.update(updates)

    # Return new context
    return AirlineAgentContext(**context_dict)


def context_diff(
    old_context: AirlineAgentContext,
    new_context: AirlineAgentContext
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


# Demo data generators for realistic test scenarios
def generate_flight_number() -> str:
    """Generate a realistic flight number."""
    airlines = ["UA", "AA", "DL", "SW", "AS", "NK", "B6"]
    airline = random.choice(airlines)
    number = random.randint(100, 9999)
    return f"{airline}{number}"


def generate_confirmation_number() -> str:
    """Generate a realistic confirmation number."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def generate_seat_number() -> str:
    """Generate a realistic seat number."""
    row = random.randint(1, 40)
    seat = random.choice(['A', 'B', 'C', 'D', 'E', 'F'])
    return f"{row}{seat}"


def generate_passenger_name() -> str:
    """Generate a realistic passenger name."""
    first_names = ["John", "Jane", "Robert", "Emily", "Michael", "Sarah",
                   "David", "Lisa", "James", "Mary"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"