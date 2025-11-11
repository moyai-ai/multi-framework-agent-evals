"""Traced runner with Langfuse observability for the Code Debug Agent.

This module wraps the agent execution with comprehensive Langfuse tracing to provide
full observability including:
- Agent execution traces
- Tool calls (as sub-spans)
- Context providers (RAG/retrieval operations)
- Sub-agent calls (for sequential agents)
"""

import asyncio
import logging
from typing import Optional, Dict, Any, AsyncIterator
from google.adk.runners import InMemoryRunner
from langfuse import observe, get_client
from src.agents import debug_agent, quick_debug_agent, AGENTS

logger = logging.getLogger(__name__)


class TracedAgentRunner:
    """Runner that provides comprehensive Langfuse tracing for Google ADK agents."""

    def __init__(
        self,
        agent_name: str = "debug_agent",
        app_name: str = "code-debug-agent-traced",
        langfuse_public_key: Optional[str] = None,
        langfuse_secret_key: Optional[str] = None,
        langfuse_host: Optional[str] = None,
    ):
        """Initialize the traced agent runner.

        Args:
            agent_name: Name of the agent to use (debug_agent, quick_debug_agent, etc.)
            app_name: Application name for the runner
            langfuse_public_key: Optional Langfuse public key (or set via env)
            langfuse_secret_key: Optional Langfuse secret key (or set via env)
            langfuse_host: Optional Langfuse host (or set via env)
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

        # Initialize Langfuse (will use environment variables if keys not provided)
        self.langfuse = get_client()
        logger.info(f"Initialized TracedAgentRunner with agent: {agent_name}")

    @observe(as_type="agent", name="debug_agent_execution")
    async def run_traced(
        self,
        prompt: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Any]:
        """Run the agent with comprehensive Langfuse tracing.

        This method wraps the agent execution with Langfuse observability,
        capturing all tool calls, context providers, and sub-agent executions.

        Args:
            prompt: User prompt/query
            user_id: Optional user identifier
            session_id: Optional session identifier
            metadata: Optional additional metadata to log

        Yields:
            Events from the agent execution
        """
        langfuse = get_client()

        # Update trace with user context
        trace_metadata = {
            "agent_name": self.agent_name,
            "app_name": self.app_name,
            "prompt_length": len(prompt),
        }
        if metadata:
            trace_metadata.update(metadata)

        langfuse.update_current_trace(
            name=f"Agent Execution: {self.agent_name}",
            user_id=user_id or "anonymous",
            session_id=session_id or "default",
            tags=["google-adk", "debug-agent", self.agent_name],
            metadata=trace_metadata,
        )

        # Update current span with input
        langfuse.update_current_span(
            input={"prompt": prompt, "agent": self.agent_name},
            metadata={"agent_model": getattr(self.agent, "model", "unknown")},
        )

        try:
            # Create or get existing session
            session = await self.runner.session_service.create_session(
                app_name=self.app_name, user_id=user_id or "user123"
            )

            logger.info(
                f"Created session: {session.session_id} for user: {user_id or 'user123'}"
            )

            # Track execution metrics
            event_count = 0
            response_parts = []

            # Run the agent and track events
            async for event in self.runner.run_async(
                session_id=session.session_id, prompt=prompt
            ):
                event_count += 1

                # Log event to Langfuse
                if hasattr(event, "__dict__"):
                    event_dict = event.__dict__
                    response_parts.append(str(event_dict))

                    # Update span with event information
                    if event_count % 5 == 0:  # Update periodically to avoid too many updates
                        langfuse.update_current_span(
                            metadata={
                                "events_processed": event_count,
                                "latest_event_type": type(event).__name__,
                            }
                        )

                yield event

            # Final update with complete results
            langfuse.update_current_span(
                output={
                    "total_events": event_count,
                    "response_summary": "\n".join(response_parts[:5]),  # First 5 events
                },
                metadata={"execution_completed": True},
            )

            logger.info(f"Agent execution completed with {event_count} events")

        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)

            # Log error to Langfuse
            langfuse.update_current_span(
                level="ERROR", status_message=str(e), metadata={"error_type": type(e).__name__}
            )

            raise

    @observe(as_type="chain", name="debug_query")
    async def query(
        self,
        prompt: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Execute a query and return the final response.

        This is a convenience method that collects all events and returns
        the final response text.

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
            # Collect response parts (this will depend on Google ADK event structure)
            response_parts.append(str(event))

        final_response = "\n".join(response_parts)

        # Update span with final output
        langfuse = get_client()
        langfuse.update_current_span(
            output={"response": final_response, "response_length": len(final_response)}
        )

        return final_response


@observe(as_type="chain", name="run_traced_scenario")
async def run_traced_scenario(
    scenario_data: Dict[str, Any],
    agent_name: str = "debug_agent",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a scenario with Langfuse tracing.

    This function is designed to work with the scenario runner and provides
    comprehensive tracing for each scenario execution.

    Args:
        scenario_data: Scenario configuration including prompt and expected results
        agent_name: Name of the agent to use
        user_id: Optional user identifier

    Returns:
        Dictionary containing execution results and metadata
    """
    langfuse = get_client()

    # Extract scenario information
    scenario_name = scenario_data.get("name", "unnamed_scenario")
    prompt = scenario_data.get("error_message", scenario_data.get("prompt", ""))

    # Update trace with scenario information
    langfuse.update_current_trace(
        name=f"Scenario: {scenario_name}",
        tags=["scenario-test", agent_name],
        metadata={"scenario_data": scenario_data},
    )

    langfuse.update_current_span(
        input={"scenario": scenario_name, "prompt": prompt},
        metadata={"agent": agent_name},
    )

    try:
        # Initialize runner
        runner = TracedAgentRunner(agent_name=agent_name)

        # Execute the scenario
        response = await runner.query(prompt=prompt, user_id=user_id, session_id=scenario_name)

        # Return results
        result = {
            "scenario_name": scenario_name,
            "success": True,
            "response": response,
            "agent_used": agent_name,
        }

        langfuse.update_current_span(output=result, metadata={"execution_success": True})

        return result

    except Exception as e:
        logger.error(f"Error running scenario {scenario_name}: {e}", exc_info=True)

        # Log error to Langfuse
        langfuse.update_current_span(
            level="ERROR", status_message=str(e), metadata={"scenario_failed": True}
        )

        return {
            "scenario_name": scenario_name,
            "success": False,
            "error": str(e),
            "agent_used": agent_name,
        }


# Convenience function for running the traced agent
@observe(as_type="chain", name="main_workflow")
async def run_debug_agent_traced(
    prompt: str,
    agent_name: str = "debug_agent",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> str:
    """Main entry point for running the traced debug agent.

    Args:
        prompt: User query/error message
        agent_name: Agent to use (debug_agent, quick_debug_agent, sequential_debug_agent)
        user_id: Optional user identifier
        session_id: Optional session identifier

    Returns:
        Agent's response as a string
    """
    runner = TracedAgentRunner(agent_name=agent_name)
    response = await runner.query(prompt=prompt, user_id=user_id, session_id=session_id)
    return response


if __name__ == "__main__":
    # Example usage
    async def main():
        # Example 1: Simple query
        response = await run_debug_agent_traced(
            prompt="ImportError: No module named 'pandas'",
            agent_name="debug_agent",
            user_id="test_user_123",
        )
        print(f"Response: {response}")

        # Example 2: Using the runner directly
        runner = TracedAgentRunner(agent_name="quick_debug_agent")
        async for event in runner.run_traced(
            prompt="TypeError: Cannot read property 'map' of undefined",
            user_id="test_user_456",
            session_id="test_session_1",
        ):
            print(f"Event: {event}")

    asyncio.run(main())
