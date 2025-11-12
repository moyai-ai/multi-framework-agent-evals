"""Traced runner with LangSmith observability for the Code Debug Agent.

This module wraps the agent execution with comprehensive LangSmith tracing to provide
full observability including:
- Agent execution traces
- Tool calls (automatically traced via @traceable decorators)
- Context providers (RAG/retrieval operations via StackExchange service)
- Sub-agent calls (for sequential agents)
- LLM generations and responses
"""

import asyncio
import logging
from typing import Optional, Dict, Any, AsyncIterator
from google.adk.runners import InMemoryRunner
from google.genai import types
from langsmith import traceable, Client
from src.agents import debug_agent, quick_debug_agent, AGENTS

logger = logging.getLogger(__name__)


class TracedAgentRunner:
    """Runner that provides comprehensive LangSmith tracing for Google ADK agents.

    This runner wraps Google ADK's InMemoryRunner and adds LangSmith observability
    to capture all aspects of agent execution including tool calls, LLM generations,
    and context retrieval operations.
    """

    def __init__(
        self,
        agent_name: str = "debug_agent",
        app_name: str = "code-debug-agent-langsmith",
        langsmith_api_key: Optional[str] = None,
        langsmith_project: Optional[str] = None,
    ):
        """Initialize the traced agent runner.

        Args:
            agent_name: Name of the agent to use (debug_agent, quick_debug_agent, etc.)
            app_name: Application name for the runner
            langsmith_api_key: Optional LangSmith API key (or set via env LANGSMITH_API_KEY)
            langsmith_project: Optional LangSmith project name (or set via env LANGSMITH_PROJECT)
        """
        self.agent_name = agent_name
        self.app_name = app_name

        # Get agent from registry
        if agent_name not in AGENTS:
            raise ValueError(
                f"Agent '{agent_name}' not found. Available agents: {list(AGENTS.keys())}"
            )

        self.agent = AGENTS[agent_name]

        # Initialize Google ADK runner
        self.runner = InMemoryRunner(agent=self.agent, app_name=app_name)

        # Initialize LangSmith client (will use environment variables if keys not provided)
        self.langsmith_client = Client(
            api_key=langsmith_api_key,
        )

        logger.info(f"Initialized TracedAgentRunner with agent: {agent_name}")

    @traceable(name="debug_agent_execution")
    async def run_traced(
        self,
        prompt: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Any]:
        """Run the agent with comprehensive LangSmith tracing.

        This method wraps the agent execution with LangSmith observability,
        capturing all tool calls, LLM generations, and sub-agent executions.
        Tool calls are automatically traced via the @traceable decorators on
        the tool functions.

        Args:
            prompt: User prompt/query
            user_id: Optional user identifier for trace grouping
            session_id: Optional session identifier for conversation tracking
            metadata: Optional additional metadata to log

        Yields:
            Events from the agent execution
        """
        try:
            # Create or get existing session
            session = await self.runner.session_service.create_session(
                app_name=self.app_name, user_id=user_id or "user123"
            )

            logger.info(
                f"Created session: {session.id} for user: {user_id or 'user123'}"
            )

            # Track execution metrics
            event_count = 0
            response_parts = []
            tool_calls_made = []

            # Create proper Content object for the message
            content = types.Content(
                parts=[types.Part(text=prompt)],
                role="user"
            )

            # Run the agent and track events
            async for event in self.runner.run_async(
                user_id=user_id or "user123",
                session_id=session.id,
                new_message=content
            ):
                event_count += 1

                # Extract event information for tracing
                if hasattr(event, "__dict__"):
                    event_dict = event.__dict__

                    # Track tool calls
                    if hasattr(event, 'tool_calls') and event.tool_calls:
                        for tool_call in event.tool_calls:
                            if hasattr(tool_call, 'function'):
                                tool_name = getattr(tool_call.function, 'name', 'unknown')
                                tool_calls_made.append(tool_name)

                    # Collect response parts
                    if hasattr(event, 'content') and event.content:
                        if hasattr(event.content, 'parts'):
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_parts.append(part.text)

                yield event

            # Return summary metadata (LangSmith automatically captures this)
            final_output = {
                "total_events": event_count,
                "tools_called": list(set(tool_calls_made)),
                "response_preview": "\n".join(response_parts[:3]) if response_parts else "No response",
            }

            logger.info(
                f"Agent execution completed: {event_count} events, "
                f"{len(tool_calls_made)} tool calls"
            )

            # The @traceable decorator will automatically capture this return value
            return final_output

        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)
            # LangSmith will automatically capture the exception
            raise

    @traceable(name="debug_query")
    async def query(
        self,
        prompt: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Execute a query and return the final response.

        This is a convenience method that collects all events and returns
        the final response text. LangSmith automatically traces this as a
        separate span within the overall trace.

        Args:
            prompt: User prompt/query
            user_id: Optional user identifier
            session_id: Optional session identifier

        Returns:
            The agent's final response as a string
        """
        response_parts = []

        async for event in self.run_traced(
            prompt=prompt, user_id=user_id, session_id=session_id
        ):
            # Collect text responses
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_parts.append(part.text)

        final_response = "\n".join(response_parts)
        return final_response


@traceable(name="run_traced_scenario")
async def run_traced_scenario(
    scenario_data: Dict[str, Any],
    agent_name: str = "debug_agent",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a scenario with LangSmith tracing.

    This function is designed to work with the scenario runner and provides
    comprehensive tracing for each scenario execution. Each scenario creates
    its own trace in LangSmith.

    Args:
        scenario_data: Scenario configuration including prompt and expected results
        agent_name: Name of the agent to use
        user_id: Optional user identifier

    Returns:
        Dictionary containing execution results and metadata
    """
    # Extract scenario information
    scenario_name = scenario_data.get("name", "unnamed_scenario")
    prompt = scenario_data.get("error_message", scenario_data.get("prompt", ""))

    try:
        # Initialize runner
        runner = TracedAgentRunner(agent_name=agent_name)

        # Execute the scenario
        response = await runner.query(
            prompt=prompt,
            user_id=user_id,
            session_id=scenario_name
        )

        # Return results
        result = {
            "scenario_name": scenario_name,
            "success": True,
            "response": response,
            "agent_used": agent_name,
        }

        return result

    except Exception as e:
        logger.error(f"Error running scenario {scenario_name}: {e}", exc_info=True)

        return {
            "scenario_name": scenario_name,
            "success": False,
            "error": str(e),
            "agent_used": agent_name,
        }


# Convenience function for running the traced agent
@traceable(name="main_workflow")
async def run_debug_agent_traced(
    prompt: str,
    agent_name: str = "debug_agent",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> str:
    """Main entry point for running the traced debug agent.

    This function creates a top-level trace in LangSmith that contains
    all sub-traces for tool calls, LLM generations, etc.

    Args:
        prompt: User query/error message
        agent_name: Agent to use (debug_agent, quick_debug_agent, sequential_debug_agent)
        user_id: Optional user identifier
        session_id: Optional session identifier for conversation tracking

    Returns:
        Agent's response as a string
    """
    runner = TracedAgentRunner(agent_name=agent_name)
    response = await runner.query(
        prompt=prompt,
        user_id=user_id,
        session_id=session_id
    )
    return response


if __name__ == "__main__":
    # Example usage demonstrating LangSmith tracing
    async def main():
        print("Running LangSmith-traced Code Debug Agent examples...")
        print("=" * 60)

        # Example 1: Simple query with debug_agent
        print("\nExample 1: Python Import Error")
        response = await run_debug_agent_traced(
            prompt="ImportError: No module named 'pandas'",
            agent_name="debug_agent",
            user_id="test_user_123",
            session_id="session_001",
        )
        print(f"Response preview: {response[:200]}...")

        # Example 2: Using quick_debug_agent for faster responses
        print("\nExample 2: JavaScript TypeError (Quick Agent)")
        response = await run_debug_agent_traced(
            prompt="TypeError: Cannot read property 'map' of undefined",
            agent_name="quick_debug_agent",
            user_id="test_user_456",
            session_id="session_002",
        )
        print(f"Response preview: {response[:200]}...")

        print("\n" + "=" * 60)
        print("Check your LangSmith dashboard to view detailed traces!")
        print("https://smith.langchain.com")

    asyncio.run(main())
