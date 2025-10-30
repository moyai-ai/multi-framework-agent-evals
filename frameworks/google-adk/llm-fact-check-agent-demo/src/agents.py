"""LLM fact-checking agents implementation using Google ADK."""

from typing import Optional, Dict, Any

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.adk.tools import google_search
from google.genai import types

from .prompts import CRITIC_PROMPT, REVISER_PROMPT

# Constants
_END_OF_EDIT_MARK = '---END-OF-EDIT---'


def _render_reference(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse:
    """Appends grounding references to the response for the critic agent."""
    del callback_context  # unused

    if (
        not llm_response.content or
        not llm_response.content.parts or
        not llm_response.grounding_metadata
    ):
        return llm_response

    references = []
    for chunk in llm_response.grounding_metadata.grounding_chunks or []:
        title, uri, text = '', '', ''
        if chunk.retrieved_context:
            title = chunk.retrieved_context.title
            uri = chunk.retrieved_context.uri
            text = chunk.retrieved_context.text
        elif chunk.web:
            title = chunk.web.title
            uri = chunk.web.uri

        parts = [s for s in (title, text) if s]
        if uri and parts:
            parts[0] = f'[{parts[0]}]({uri})'
        if parts:
            references.append('* ' + ': '.join(parts) + '\n')

    if references:
        reference_text = ''.join(['\n\nReference:\n\n'] + references)
        llm_response.content.parts.append(types.Part(text=reference_text))

    if all(part.text is not None for part in llm_response.content.parts):
        all_text = '\n'.join(part.text for part in llm_response.content.parts)
        llm_response.content.parts[0].text = all_text
        del llm_response.content.parts[1:]

    return llm_response


def _remove_end_of_edit_mark(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse:
    """Removes the END-OF-EDIT marker from the reviser agent's response."""
    del callback_context  # unused

    if not llm_response.content or not llm_response.content.parts:
        return llm_response

    for idx, part in enumerate(llm_response.content.parts):
        if part.text and _END_OF_EDIT_MARK in part.text:
            del llm_response.content.parts[idx + 1:]
            part.text = part.text.split(_END_OF_EDIT_MARK, 1)[0]
            break

    return llm_response


# Define the critic agent
critic_agent = Agent(
    model='gemini-2.5-flash',
    name='critic_agent',
    instruction=CRITIC_PROMPT,
    tools=[google_search],
    after_model_callback=_render_reference,
)

# Define the reviser agent
reviser_agent = Agent(
    model='gemini-2.5-flash',
    name='reviser_agent',
    instruction=REVISER_PROMPT,
    after_model_callback=_remove_end_of_edit_mark,
)

# Define the root sequential agent that orchestrates critic -> reviser
llm_fact_check_agent = SequentialAgent(
    name='llm_fact_check_agent',
    description=(
        'An automated fact-checking system that verifies claims in LLM-generated text. '
        'First, the critic agent identifies and verifies all claims using web search. '
        'Then, the reviser agent corrects any inaccuracies based on the findings.'
    ),
    sub_agents=[critic_agent, reviser_agent]
)

# Agent registry for easy lookup
AGENTS: Dict[str, Agent] = {
    'llm_fact_check_agent': llm_fact_check_agent,
    'critic_agent': critic_agent,
    'reviser_agent': reviser_agent,
}


def get_agent_by_name(name: str) -> Optional[Agent]:
    """Get an agent by name with exact and partial matching."""
    # First try exact match
    if name in AGENTS:
        return AGENTS[name]

    # Try partial match (case-insensitive)
    name_lower = name.lower()
    for agent_name, agent in AGENTS.items():
        if name_lower in agent_name.lower():
            return agent

    return None


def get_initial_agent() -> Agent:
    """Get the initial/root agent for the fact-checking system."""
    return llm_fact_check_agent


def list_agents() -> list:
    """List all available agents with their descriptions."""
    agents = []
    for name, agent in AGENTS.items():
        agent_info = {
            'name': name,
            'type': type(agent).__name__,
            'model': getattr(agent, 'model', 'N/A'),
        }
        if hasattr(agent, 'description'):
            agent_info['description'] = agent.description
        elif hasattr(agent, 'instruction'):
            # Get first line of instruction as description
            agent_info['description'] = agent.instruction.strip().split('\n')[0][:100]
        agents.append(agent_info)
    return agents