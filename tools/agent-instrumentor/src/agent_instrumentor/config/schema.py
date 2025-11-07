"""Configuration schema for instrumentation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Literal


class InstrumentationLevel(str, Enum):
    """Level of instrumentation detail."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class InstrumentationTarget(str, Enum):
    """Components to instrument."""
    TOOLS = "tools"
    LLM_CALLS = "llm_calls"
    RAG = "rag"
    MEMORY = "memory"
    CHAINS = "chains"
    ERRORS = "errors"
    SUB_AGENTS = "sub_agents"
    PROMPTS = "prompts"


class CostLimit(str, Enum):
    """Cost/overhead limits for instrumentation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PerformanceImpact(str, Enum):
    """Acceptable performance impact."""
    MINIMAL = "minimal"
    ACCEPTABLE = "acceptable"
    DETAILED = "detailed"


@dataclass
class InstrumentationConfig:
    """Configuration for agent instrumentation."""

    level: InstrumentationLevel = InstrumentationLevel.STANDARD
    targets: List[InstrumentationTarget] = field(default_factory=lambda: [
        InstrumentationTarget.TOOLS,
        InstrumentationTarget.LLM_CALLS,
        InstrumentationTarget.CHAINS,
    ])
    platform: str = "langfuse"
    cost_limit: CostLimit = CostLimit.MEDIUM
    performance_impact: PerformanceImpact = PerformanceImpact.ACCEPTABLE

    # Optional: Specific frameworks to instrument (empty = all detected)
    frameworks: List[str] = field(default_factory=list)

    # Optional: Files to exclude from instrumentation
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "**/test_*.py",
        "**/*_test.py",
        "**/tests/**",
    ])

    def should_instrument_target(self, target: InstrumentationTarget) -> bool:
        """Check if a target should be instrumented."""
        return target in self.targets

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "targets": [t.value for t in self.targets],
            "platform": self.platform,
            "cost_limit": self.cost_limit.value,
            "performance_impact": self.performance_impact.value,
            "frameworks": self.frameworks,
            "exclude_patterns": self.exclude_patterns,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InstrumentationConfig":
        """Create from dictionary."""
        return cls(
            level=InstrumentationLevel(data.get("level", "standard")),
            targets=[InstrumentationTarget(t) for t in data.get("targets", [])],
            platform=data.get("platform", "langfuse"),
            cost_limit=CostLimit(data.get("cost_limit", "medium")),
            performance_impact=PerformanceImpact(data.get("performance_impact", "acceptable")),
            frameworks=data.get("frameworks", []),
            exclude_patterns=data.get("exclude_patterns", []),
        )
