"""
Agent Instrumentor - Autonomous instrumentation of multi-framework agents.

Automatically instruments agents across LangChain, OpenAI Agents SDK, CrewAI,
Pydantic AI, Google ADK, and Claude Agent SDK with observability platforms
like Langfuse.
"""

__version__ = "0.1.0"

from .agents import instrument_codebase_with_agent
from .platforms import list_platforms, get_platform
from .config import (
    InstrumentationConfig,
    InstrumentationLevel,
    InstrumentationTarget,
    PRESET_MINIMAL,
    PRESET_STANDARD,
    PRESET_COMPREHENSIVE,
)

__all__ = [
    "instrument_codebase_with_agent",
    "list_platforms",
    "get_platform",
    "InstrumentationConfig",
    "InstrumentationLevel",
    "InstrumentationTarget",
    "PRESET_MINIMAL",
    "PRESET_STANDARD",
    "PRESET_COMPREHENSIVE",
]
