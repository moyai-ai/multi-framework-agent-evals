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
import os
from typing import Optional, Dict, Any, AsyncIterator
from google.adk.runners import InMemoryRunner
from google.genai import types
from langfuse import observe, get_client
from src.agents import debug_agent, quick_debug_agent, AGENTS

# Configure OpenTelemetry resource attributes for better trace naming
os.environ.setdefault("OTEL_SERVICE_NAME", "code-debug-agent")
os.environ.setdefault("OTEL_RESOURCE_ATTRIBUTES", "service.name=code-debug-agent,deployment.environment=production")

# Note: Google ADK's OpenTelemetry instrumentation creates generic "invocation" and "call"
# span names. We use Langfuse's update_current_trace() to override the trace name, but this
# only affects the Langfuse trace name, not the underlying OpenTelemetry span names.
# The Langfuse UI will show our custom trace names (e.g., "Code Debug: debug_agent"),
# which is what matters for observability.

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

        Note: We do NOT use @observe() decorator here because Google ADK already
        creates OpenTelemetry traces. Using @observe() would create a child trace
        instead of updating the root trace. By calling update_current_trace()
        without @observe(), we update the actual Google ADK root trace.

        Args:
            prompt: User prompt/query
            user_id: Optional user identifier
            session_id: Optional session identifier
            metadata: Optional additional metadata to log

        Yields:
            Events from the agent execution
        """
        langfuse = get_client()

        # Get the current OpenTelemetry trace context
        try:
            from opentelemetry import trace
            current_span = trace.get_current_span()
            trace_id = None
            if current_span and current_span.is_recording():
                # Get the trace ID from OpenTelemetry span
                trace_id = format(current_span.get_span_context().trace_id, '032x')
                print(f"[TRACE] OpenTelemetry trace ID: {trace_id}")
        except Exception as e:
            print(f"[TRACE] Could not get OpenTelemetry trace ID: {e}")
            trace_id = None

        # Update trace with user context and descriptive naming
        # This updates the ROOT trace created by Google ADK's OpenTelemetry instrumentation
        trace_metadata = {
            "agent_name": self.agent_name,
            "app_name": self.app_name,
            "prompt_length": len(prompt),
            "framework": "google-adk",
            "agent_type": "code-debug-agent",
            "prompt_preview": prompt[:200],
        }
        if metadata:
            trace_metadata.update(metadata)

        # Use descriptive trace name that shows in Langfuse UI
        # This replaces the generic "invocation" name from Google ADK
        try:
            langfuse.update_current_trace(
                name=f"Code Debug: {self.agent_name}",
                user_id=user_id or "anonymous",
                session_id=session_id or "default",
                tags=["google-adk", "code-debug", self.agent_name, "production"],
                metadata=trace_metadata,
                input={"prompt": prompt, "agent": self.agent_name},
            )
            print(f"[TRACE] Updated Langfuse trace with name: Code Debug: {self.agent_name}")
        except Exception as e:
            print(f"[TRACE] Could not update Langfuse trace: {e}")
            import traceback
            traceback.print_exc()
            # If update fails, try to create a manual trace entry
            if trace_id:
                try:
                    langfuse.trace(
                        id=trace_id,
                        name=f"Code Debug: {self.agent_name}",
                        user_id=user_id or "anonymous",
                        session_id=session_id or "default",
                        tags=["google-adk", "code-debug", self.agent_name, "production"],
                        metadata=trace_metadata,
                        input={"prompt": prompt, "agent": self.agent_name},
                    )
                    print(f"[TRACE] Created manual Langfuse trace entry with ID: {trace_id}")
                except Exception as e2:
                    print(f"[TRACE] Could not create manual trace entry: {e2}")
                    traceback.print_exc()

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

                # Log event to Langfuse
                if hasattr(event, "__dict__"):
                    event_dict = event.__dict__
                    response_parts.append(str(event_dict))

                    # Update trace metadata periodically
                    if event_count % 10 == 0:  # Update every 10 events
                        langfuse.update_current_trace(
                            metadata={
                                "events_processed": event_count,
                                "latest_event_type": type(event).__name__,
                            }
                        )

                yield event

            # Final update with complete results
            langfuse.update_current_trace(
                output={
                    "total_events": event_count,
                    "response_summary": "\n".join(response_parts[:5]),  # First 5 events
                },
                metadata={
                    **trace_metadata,
                    "execution_completed": True,
                    "total_events_processed": event_count,
                },
            )

            logger.info(f"Agent execution completed with {event_count} events")

        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)

            # Log error to Langfuse trace
            langfuse.update_current_trace(
                metadata={
                    **trace_metadata,
                    "error_occurred": True,
                    "error_type": type(e).__name__,
                    "error_details": str(e)[:500],  # Truncate long errors
                }
            )

            raise

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

        # Update trace with final output
        langfuse = get_client()
        langfuse.update_current_trace(
            output={"response": final_response, "response_length": len(final_response)},
            metadata={"query_completed": True}
        )

        return final_response


async def run_traced_scenario(
    scenario_data: Dict[str, Any],
    agent_name: str = "debug_agent",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a scenario with Langfuse tracing.

    This function is designed to work with the scenario runner and provides
    comprehensive tracing for each scenario execution.

    Note: We don't use @observe() here because the TracedAgentRunner will
    update the root Google ADK trace. Using @observe() would create an extra
    child trace that we don't need.

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
    programming_language = scenario_data.get("programming_language", "unknown")

    # Update root trace with scenario information
    langfuse.update_current_trace(
        name=f"Scenario: {scenario_name}",
        tags=["scenario-test", "evaluation", agent_name, programming_language],
        metadata={
            "scenario_name": scenario_name,
            "programming_language": programming_language,
            "agent_name": agent_name,
            "test_type": "scenario_execution",
        },
        input={"scenario": scenario_name, "prompt": prompt, "language": programming_language},
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

        langfuse.update_current_trace(
            output=result,
            metadata={
                "execution_success": True,
                "scenario_completed": True,
                "response_length": len(response),
            }
        )

        return result

    except Exception as e:
        logger.error(f"Error running scenario {scenario_name}: {e}", exc_info=True)

        # Log error to Langfuse
        langfuse.update_current_trace(
            metadata={
                "scenario_failed": True,
                "error_type": type(e).__name__,
                "scenario_name": scenario_name,
                "error_details": str(e)[:500],
            }
        )

        return {
            "scenario_name": scenario_name,
            "success": False,
            "error": str(e),
            "agent_used": agent_name,
        }


# Convenience function for running the traced agent
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
