"""Wrapper for running the Code Debug Agent with evaluation tracking."""

from __future__ import annotations

import importlib
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.adk.runners import InMemoryRunner
from google.genai import types

from src.data_models import DebugAgentExample

# Configure access to the base Google ADK agent package
REPO_ROOT = Path(__file__).resolve().parents[5]  # Go up to .conductor/cambridge
AGENT_BASE_PATH = REPO_ROOT / "frameworks" / "google-adk" / "code-debug-agent-demo"
OBSERVABILITY_BASE_PATH = REPO_ROOT / "observability"
OBSERVABILITY_PROVIDER_PATHS = {
    "langfuse": OBSERVABILITY_BASE_PATH / "langfuse" / "google-adk" / "code-debug-agent-demo",
    "langsmith": OBSERVABILITY_BASE_PATH / "langsmith" / "google-adk" / "code-debug-agent-demo",
}
_TRACING_MODULES = (
    "src",
    "src.agents",
    "src.runner",
    "src.tools",
    "src.services",
    "src.prompts",
    "src.traced_runner",
)
_TRACED_RUNNER_CACHE: Dict[str, Any] = {}


# Import the agent's get_agent_by_name function
# We need to be careful about namespace collision between evaluation's src/ and agent's src/
def _import_agent_function():
    """Import get_agent_by_name from the agent's src.agents module."""
    saved_src = sys.modules.get("src")
    saved_src_agents = sys.modules.get("src.agents")

    try:
        # Remove src from sys.modules temporarily
        if "src" in sys.modules:
            del sys.modules["src"]
        if "src.agents" in sys.modules:
            del sys.modules["src.agents"]

        # Add agent base path and import
        if str(AGENT_BASE_PATH) not in sys.path:
            sys.path.insert(0, str(AGENT_BASE_PATH))

        # Import the agents module from agent's src
        import src.agents as agent_module

        return agent_module.get_agent_by_name

    finally:
        # Restore the evaluation's src module
        if saved_src is not None:
            sys.modules["src"] = saved_src
        elif "src" in sys.modules:
            del sys.modules["src"]

        if saved_src_agents is not None:
            sys.modules["src.agents"] = saved_src_agents
        elif "src.agents" in sys.modules:
            del sys.modules["src.agents"]


get_agent_by_name = _import_agent_function()

logger = logging.getLogger(__name__)

_NOISY_DEP_LOGGERS = (
    "google_adk.google.adk.models.google_llm",
    "google_adk.google.adk.runners",
    "google_genai.types",  # Suppress function_call warnings
)


def _configure_dependency_logging(level: int = logging.WARNING) -> None:
    """Reduce verbosity from dependency loggers that default to INFO."""
    for logger_name in _NOISY_DEP_LOGGERS:
        noisy_logger = logging.getLogger(logger_name)
        # Suppress function call warnings from google_genai.types completely
        if logger_name == "google_genai.types":
            noisy_logger.setLevel(logging.ERROR)
        else:
            noisy_logger.setLevel(level)


_configure_dependency_logging()


def _import_traced_runner_class(provider: str):
    """Dynamically import the traced runner implementation for a provider."""
    normalized_provider = provider.lower()
    if normalized_provider not in OBSERVABILITY_PROVIDER_PATHS:
        raise ValueError(f"Unsupported tracing provider: {provider}")

    if normalized_provider in _TRACED_RUNNER_CACHE:
        return _TRACED_RUNNER_CACHE[normalized_provider]

    provider_path = OBSERVABILITY_PROVIDER_PATHS[normalized_provider]
    if not provider_path.exists():
        raise ImportError(
            f"Tracing provider path not found: {provider_path}"
        )

    saved_modules: Dict[str, Any] = {}
    for module_name in _TRACING_MODULES:
        if module_name in sys.modules:
            saved_modules[module_name] = sys.modules[module_name]
            del sys.modules[module_name]

    try:
        if str(provider_path) not in sys.path:
            sys.path.insert(0, str(provider_path))
            remove_path = True
        else:
            remove_path = False

        traced_module = importlib.import_module("src.traced_runner")
        traced_runner_class = getattr(traced_module, "TracedAgentRunner")
        _TRACED_RUNNER_CACHE[normalized_provider] = traced_runner_class
        return traced_runner_class

    finally:
        if remove_path:
            try:
                sys.path.remove(str(provider_path))
            except ValueError:
                pass

        # Clean up imported observability modules
        for module_name in _TRACING_MODULES:
            if module_name in sys.modules and module_name not in saved_modules:
                del sys.modules[module_name]

        for module_name, module in saved_modules.items():
            sys.modules[module_name] = module


class DebugAgentRunner:
    """Wrapper for running the Code Debug Agent and collecting evaluation data."""

    def __init__(
        self,
        agent_name: str = "debug_agent",
        use_langfuse: bool = False,
        use_langsmith: bool = False,
    ):
        """Initialize the agent runner.

        Args:
            agent_name: Name of the agent to use (debug_agent, quick_debug_agent, etc.)
            use_langfuse: Enable Langfuse tracing backend
            use_langsmith: Enable LangSmith tracing backend
        """
        if use_langfuse and use_langsmith:
            raise ValueError("Cannot enable both Langfuse and LangSmith tracing")

        self.agent_name = agent_name
        self.agent = get_agent_by_name(agent_name)
        if not self.agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        self.use_langfuse = use_langfuse
        self.use_langsmith = use_langsmith
        self.tracing_provider: Optional[str] = None
        self._traced_runner = None

        if self.use_langfuse:
            self.tracing_provider = "langfuse"
        elif self.use_langsmith:
            self.tracing_provider = "langsmith"

        if self.tracing_provider:
            traced_runner_class = _import_traced_runner_class(self.tracing_provider)
            self._traced_runner = traced_runner_class(agent_name=agent_name)
            self.runner = None
        else:
            self.runner = InMemoryRunner(
                agent=self.agent,
                app_name=f"{agent_name}_eval"
            )

        self.session = None

    async def setup(self):
        """Initialize the runner and create a session."""
        if self.tracing_provider:
            # Tracing runners manage their own sessions
            return

        self.session = await self.runner.session_service.create_session(
            app_name=self.runner.app_name,
            user_id="eval_user"
        )
        logger.info(f"Created session: {self.session.id}")

    async def run_debug_query(
        self,
        error_message: str,
        programming_language: Optional[str] = None,
        framework: Optional[str] = None,
        expected_tools: Optional[List[str]] = None,
        expected_keywords: Optional[List[str]] = None,
        conversation: Optional[List[Dict[str, Any]]] = None,
    ) -> DebugAgentExample:
        """Run a debug query and return an evaluation example.

        Args:
            error_message: The error message to debug
            programming_language: Programming language (e.g., python, javascript)
            framework: Framework if applicable (e.g., react, django)
            expected_tools: Expected tools the agent should call
            expected_keywords: Keywords expected in the solution
            conversation: Optional multi-turn conversation definition

        Returns:
            DebugAgentExample ready for evaluation
        """
        if not self.session and not self.tracing_provider:
            await self.setup()

        start_time = datetime.now()

        prompts = self._build_conversation_prompts(
            error_message=error_message,
            programming_language=programming_language,
            framework=framework,
            conversation=conversation,
        )

        # Track execution
        response_parts: List[str] = []
        tools_called: List[str] = []
        retrieval_context: List[str] = []

        try:
            if self.tracing_provider:
                await self._run_with_tracing_backend(
                    prompts=prompts,
                    response_parts=response_parts,
                    tools_called=tools_called,
                    metadata={
                        "programming_language": programming_language,
                        "framework": framework,
                        "expected_tools": expected_tools,
                        "conversation_turns": len(prompts),
                    },
                )
            else:
                await self._run_with_inmemory_runner(
                    prompts=prompts,
                    response_parts=response_parts,
                    tools_called=tools_called,
                )

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Error running agent: %s", exc, exc_info=True)
            response_parts.append(f"ERROR: {exc}")

        execution_time = (datetime.now() - start_time).total_seconds()
        agent_response = "\n".join(response_parts)

        # Determine error type from message
        error_type = None
        error_lower = error_message.lower()
        if "importerror" in error_lower or "modulenotfound" in error_lower:
            error_type = "ImportError"
        elif "typeerror" in error_lower:
            error_type = "TypeError"
        elif "attributeerror" in error_lower:
            error_type = "AttributeError"
        elif "syntaxerror" in error_lower:
            error_type = "SyntaxError"
        elif "valueerror" in error_lower:
            error_type = "ValueError"

        # Create evaluation example
        example = DebugAgentExample(
            error_message=error_message,
            programming_language=programming_language,
            framework=framework,
            agent_response=agent_response,
            tools_called=tools_called,
            expected_tools=expected_tools,
            expected_solution_keywords=expected_keywords,
            retrieval_context=retrieval_context if retrieval_context else None,
            execution_time=execution_time,
            error_type=error_type,
            input="\n\n".join(prompts),
            actual_output=agent_response,
        )

        return example

    async def _run_with_inmemory_runner(
        self,
        prompts: List[str],
        response_parts: List[str],
        tools_called: List[str],
    ) -> None:
        """Execute prompts using the in-memory runner (no tracing)."""
        for turn in prompts:
            content = types.Content(
                parts=[types.Part(text=turn)],
                role="user",
            )

            async for event in self.runner.run_async(
                user_id=self.session.user_id,
                session_id=self.session.id,
                new_message=content,
            ):
                self._extract_event_content(event, response_parts)
                tools_called.extend(self._extract_tool_calls(event))

    async def _run_with_tracing_backend(
        self,
        prompts: List[str],
        response_parts: List[str],
        tools_called: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Execute prompts using a traced runner (Langfuse or LangSmith)."""
        if not self._traced_runner:
            raise RuntimeError("Tracing backend is not initialized")

        user_id = "eval_user"
        session_id = f"{self.agent_name}_eval_session"
        combined_prompt = "\n\n".join(prompts)

        async for event in self._traced_runner.run_traced(
            prompt=combined_prompt,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
        ):
            self._extract_event_content(event, response_parts)
            tools_called.extend(self._extract_tool_calls(event))

    def _build_conversation_prompts(
        self,
        error_message: str,
        programming_language: Optional[str],
        framework: Optional[str],
        conversation: Optional[List[Dict[str, Any]]],
    ) -> List[str]:
        """Create the ordered list of prompts to replay for the runner."""
        if conversation:
            prompts = [
                turn.get("user_input") or error_message
                for turn in conversation
                if turn.get("user_input")
            ]
            if prompts:
                return prompts

        base_parts = [error_message]
        if programming_language:
            base_parts.append(f"Language: {programming_language}")
        if framework:
            base_parts.append(f"Framework: {framework}")
        return ["\n".join(base_parts)]

    @staticmethod
    def _extract_event_content(event: Any, response_parts: List[str]) -> None:
        """Capture model text emitted in a runner event."""
        content = getattr(event, "content", None)
        if not content or not hasattr(content, "parts"):
            return

        for part in content.parts:
            text = getattr(part, "text", None)
            if text:
                response_parts.append(text)

    @staticmethod
    def _extract_tool_calls(event: Any) -> List[str]:
        """Return tool names invoked in a runner event."""
        tool_calls = getattr(event, "tool_calls", None)
        if not tool_calls:
            return []

        names = []
        for tool_call in tool_calls:
            function = getattr(tool_call, "function", None)
            if function:
                names.append(getattr(function, "name", "unknown"))
        return names


async def run_agent_with_tracing(
    error_message: str,
    agent_name: str = "debug_agent",
    programming_language: Optional[str] = None,
    framework: Optional[str] = None,
    use_langfuse: bool = False,
    use_langsmith: bool = False,
) -> DebugAgentExample:
    """Run agent with optional observability tracing."""
    runner = DebugAgentRunner(
        agent_name=agent_name,
        use_langfuse=use_langfuse,
        use_langsmith=use_langsmith,
    )
    example = await runner.run_debug_query(
        error_message=error_message,
        programming_language=programming_language,
        framework=framework,
    )

    return example
