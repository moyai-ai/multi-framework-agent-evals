"""Preset configurations for common use cases."""

from .schema import (
    InstrumentationConfig,
    InstrumentationLevel,
    InstrumentationTarget,
    CostLimit,
    PerformanceImpact,
)


PRESET_MINIMAL = InstrumentationConfig(
    level=InstrumentationLevel.MINIMAL,
    targets=[
        InstrumentationTarget.LLM_CALLS,
    ],
    platform="langfuse",
    cost_limit=CostLimit.LOW,
    performance_impact=PerformanceImpact.MINIMAL,
)
"""Minimal instrumentation: Only track LLM calls for basic usage monitoring."""


PRESET_STANDARD = InstrumentationConfig(
    level=InstrumentationLevel.STANDARD,
    targets=[
        InstrumentationTarget.TOOLS,
        InstrumentationTarget.LLM_CALLS,
        InstrumentationTarget.CHAINS,
        InstrumentationTarget.ERRORS,
    ],
    platform="langfuse",
    cost_limit=CostLimit.MEDIUM,
    performance_impact=PerformanceImpact.ACCEPTABLE,
)
"""Standard instrumentation: Track tools, LLM calls, chains, and errors."""


PRESET_COMPREHENSIVE = InstrumentationConfig(
    level=InstrumentationLevel.COMPREHENSIVE,
    targets=[
        InstrumentationTarget.TOOLS,
        InstrumentationTarget.LLM_CALLS,
        InstrumentationTarget.RAG,
        InstrumentationTarget.MEMORY,
        InstrumentationTarget.CHAINS,
        InstrumentationTarget.ERRORS,
        InstrumentationTarget.SUB_AGENTS,
        InstrumentationTarget.PROMPTS,
    ],
    platform="langfuse",
    cost_limit=CostLimit.HIGH,
    performance_impact=PerformanceImpact.DETAILED,
)
"""Comprehensive instrumentation: Track all agent components for deep observability."""
