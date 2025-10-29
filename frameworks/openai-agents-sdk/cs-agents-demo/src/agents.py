"""
Agent definitions for the Airline Customer Service System.

This module defines all 5 specialized agents:
- Triage Agent (entry point)
- Seat Booking Agent
- Flight Status Agent
- FAQ Agent
- Cancellation Agent
"""

from typing import Optional, Dict, Any
from agents import Agent, RunContextWrapper, handoff
from .context import (
    AirlineAgentContext,
    generate_flight_number,
    generate_confirmation_number,
    generate_seat_number,
    generate_passenger_name
)
from .tools import (
    faq_lookup_tool,
    update_seat,
    flight_status_tool,
    baggage_tool,
    display_seat_map,
    cancel_flight
)
from .guardrails import relevance_guardrail, jailbreak_guardrail


# Handoff prompt prefix used by all agents
RECOMMENDED_PROMPT_PREFIX = """You have access to agents that are more specialized in certain topics.
You can hand off to them if you think they are better suited to handle the user's request.
Don't mention the handoffs or the agents to the user.

"""


# ===== HANDOFF HOOKS =====
async def on_seat_booking_handoff(context: RunContextWrapper[AirlineAgentContext]) -> None:
    """
    Initialize context when handing off to Seat Booking Agent.

    Generates flight and confirmation numbers if not already present.
    """
    if not context.context.flight_number:
        context.context.flight_number = generate_flight_number()
    if not context.context.confirmation_number:
        context.context.confirmation_number = generate_confirmation_number()
    if not context.context.passenger_name:
        context.context.passenger_name = generate_passenger_name()
    if not context.context.seat_number:
        context.context.seat_number = generate_seat_number()

    context.context.conversation_stage = "seat_booking"


async def on_cancellation_handoff(context: RunContextWrapper[AirlineAgentContext]) -> None:
    """
    Initialize context when handing off to Cancellation Agent.

    Generates booking details if not already present.
    """
    if not context.context.flight_number:
        context.context.flight_number = generate_flight_number()
    if not context.context.confirmation_number:
        context.context.confirmation_number = generate_confirmation_number()
    if not context.context.passenger_name:
        context.context.passenger_name = generate_passenger_name()
    if not context.context.seat_number:
        context.context.seat_number = generate_seat_number()

    context.context.conversation_stage = "cancellation"


# ===== DYNAMIC INSTRUCTIONS =====
def seat_booking_instructions(
    run_context: RunContextWrapper[AirlineAgentContext],
    agent: Agent[AirlineAgentContext]
) -> str:
    """
    Dynamic instructions for Seat Booking Agent.

    Includes current context values in the instructions.
    """
    context = run_context.context
    base_instructions = f"""{RECOMMENDED_PROMPT_PREFIX}
You are a Seat Booking Agent for an airline customer service system.

Your role is to help customers change or select their seats on flights.

Current Customer Information:
- Confirmation Number: {context.confirmation_number or 'Not provided'}
- Flight Number: {context.flight_number or 'Not provided'}
- Current Seat: {context.seat_number or 'Not assigned'}
- Passenger Name: {context.passenger_name or 'Not provided'}

Your workflow:
1. Confirm the customer's confirmation number and flight number
2. Ask what seat they would like or offer to show the seat map
3. Use the update_seat tool to make the change
4. Confirm the change with the customer

Available tools:
- update_seat: Change the passenger's seat assignment
- display_seat_map: Show an interactive seat map

Important:
- Always be friendly and professional
- Validate seat selections (e.g., 12A, 23F format)
- Inform customers about any seat restrictions or fees
- If the customer needs help with non-seat related issues, hand off to the Triage Agent
"""
    return base_instructions


def flight_status_instructions(
    run_context: RunContextWrapper[AirlineAgentContext],
    agent: Agent[AirlineAgentContext]
) -> str:
    """
    Dynamic instructions for Flight Status Agent.

    Includes current context values in the instructions.
    """
    context = run_context.context
    base_instructions = f"""{RECOMMENDED_PROMPT_PREFIX}
You are a Flight Status Agent for an airline customer service system.

Your role is to provide flight status information and updates.

Current Customer Information:
- Flight Number: {context.flight_number or 'Not provided'}
- Confirmation Number: {context.confirmation_number or 'Not provided'}
- Passenger Name: {context.passenger_name or 'Not provided'}

Your workflow:
1. Confirm the flight number or confirmation number
2. Use the flight_status_tool to check the status
3. Provide clear information about delays, gates, and timing
4. Offer additional help if needed

Available tools:
- flight_status_tool: Check current flight status

Important:
- Be clear about any delays or changes
- Provide gate information when available
- Suggest next steps (e.g., proceed to gate, check later)
- If the customer needs help with other issues, hand off to the Triage Agent
"""
    return base_instructions


def cancellation_instructions(
    run_context: RunContextWrapper[AirlineAgentContext],
    agent: Agent[AirlineAgentContext]
) -> str:
    """
    Dynamic instructions for Cancellation Agent.

    Includes current context values in the instructions.
    """
    context = run_context.context
    base_instructions = f"""{RECOMMENDED_PROMPT_PREFIX}
You are a Cancellation Agent for an airline customer service system.

Your role is to help customers cancel their flight bookings.

Current Customer Information:
- Confirmation Number: {context.confirmation_number or 'Not provided'}
- Flight Number: {context.flight_number or 'Not provided'}
- Passenger Name: {context.passenger_name or 'Not provided'}
- Seat: {context.seat_number or 'Not assigned'}

Your workflow:
1. Confirm the customer's confirmation and flight numbers
2. Verify they want to cancel (get explicit confirmation)
3. Use the cancel_flight tool to process the cancellation
4. Provide refund information and next steps

Available tools:
- cancel_flight: Process flight cancellation

Important:
- Always get explicit confirmation before cancelling
- Clearly explain refund policies and timelines
- Provide the cancellation confirmation number
- If the customer changes their mind, hand off to appropriate agent
"""
    return base_instructions


# ===== AGENT DEFINITIONS =====

# Triage Agent - Entry point that routes to specialists
triage_agent = Agent[AirlineAgentContext](
    name="Triage Agent",
    model="gpt-4o",
    handoff_description="Route to the Triage Agent for general inquiries and request routing",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are a Triage Agent for an airline customer service system.

Your primary role is to understand customer needs and route them to the appropriate specialist agent.

You can hand off to:
- Seat Booking Agent: For seat changes and selection
- Flight Status Agent: For flight status, delays, and gate information
- FAQ Agent: For general policy questions (baggage, wifi, etc.)
- Cancellation Agent: For flight cancellations

Your workflow:
1. Greet the customer warmly
2. Understand their primary need
3. Hand off to the appropriate specialist immediately

Important:
- Don't try to handle specialized requests yourself
- Be concise - just understand and route
- Always be professional and friendly
""",
    handoffs=[],  # Will be set after all agents are defined
    input_guardrails=[relevance_guardrail, jailbreak_guardrail]
)


# Seat Booking Agent
seat_booking_agent = Agent[AirlineAgentContext](
    name="Seat Booking Agent",
    model="gpt-4o",
    handoff_description="Hand off to Seat Booking Agent for seat selection and changes",
    instructions=seat_booking_instructions,
    tools=[update_seat, display_seat_map],
    handoffs=[
        handoff(
            agent=triage_agent,
            on_handoff=None
        )
    ]
)


# Flight Status Agent
flight_status_agent = Agent[AirlineAgentContext](
    name="Flight Status Agent",
    model="gpt-4o",
    handoff_description="Hand off to Flight Status Agent for flight status and gate information",
    instructions=flight_status_instructions,
    tools=[flight_status_tool],
    handoffs=[
        handoff(
            agent=triage_agent,
            on_handoff=None
        )
    ]
)


# FAQ Agent
faq_agent = Agent[AirlineAgentContext](
    name="FAQ Agent",
    model="gpt-4o",
    handoff_description="Hand off to FAQ Agent for general policy questions",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
You are an FAQ Agent for an airline customer service system.

Your role is to answer general questions about airline policies and services.

You can answer questions about:
- Baggage policies and fees
- Wi-Fi availability and pricing
- Seat selection policies
- Check-in procedures
- Meal services
- General airline policies

Available tools:
- faq_lookup_tool: Look up FAQ answers
- baggage_tool: Get specific baggage information

Important:
- Provide clear, accurate information
- If the question is too specific or requires action, hand off to Triage Agent
- Be friendly and helpful
""",
    tools=[faq_lookup_tool, baggage_tool],
    handoffs=[
        handoff(
            agent=triage_agent,
            on_handoff=None
        )
    ]
)


# Cancellation Agent
cancellation_agent = Agent[AirlineAgentContext](
    name="Cancellation Agent",
    model="gpt-4o",
    handoff_description="Hand off to Cancellation Agent for flight cancellations",
    instructions=cancellation_instructions,
    tools=[cancel_flight],
    handoffs=[
        handoff(
            agent=triage_agent,
            on_handoff=None
        )
    ]
)


# Now set the Triage Agent's handoffs with the proper hooks
triage_agent.handoffs = [
    handoff(
        agent=seat_booking_agent,
        on_handoff=on_seat_booking_handoff
    ),
    handoff(
        agent=flight_status_agent,
        on_handoff=None
    ),
    handoff(
        agent=faq_agent,
        on_handoff=None
    ),
    handoff(
        agent=cancellation_agent,
        on_handoff=on_cancellation_handoff
    )
]


# Agent registry for easy lookup
AGENTS: Dict[str, Agent[AirlineAgentContext]] = {
    "triage": triage_agent,
    "seat_booking": seat_booking_agent,
    "flight_status": flight_status_agent,
    "faq": faq_agent,
    "cancellation": cancellation_agent
}


def get_agent_by_name(name: str) -> Optional[Agent[AirlineAgentContext]]:
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


def get_initial_agent() -> Agent[AirlineAgentContext]:
    """
    Get the initial agent for new conversations.

    Returns:
        The Triage Agent
    """
    return triage_agent


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
            "description": agent.handoff_description or "No description available",
            "tools": [tool.name if hasattr(tool, 'name') else str(tool) for tool in (agent.tools or [])],
            "can_handoff_to": [
                h.agent.name if hasattr(h, 'agent') else str(h)
                for h in (agent.handoffs or [])
            ]
        }
        for key, agent in AGENTS.items()
    ]