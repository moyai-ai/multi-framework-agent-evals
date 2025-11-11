"""
Configuration and context management for the Static Code Analysis Agent with LangSmith.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()


@dataclass
class AnalysisContext:
    """Context for code analysis operations."""

    repository_url: Optional[str] = None
    repository_owner: Optional[str] = None
    repository_name: Optional[str] = None
    analysis_type: str = "security"  # security, quality, dependencies
    target_files: list[str] = field(default_factory=list)
    results: list[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "repository_url": self.repository_url,
            "repository_owner": self.repository_owner,
            "repository_name": self.repository_name,
            "analysis_type": self.analysis_type,
            "target_files": self.target_files,
            "results": self.results,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisContext":
        """Create context from dictionary."""
        return cls(
            repository_url=data.get("repository_url"),
            repository_owner=data.get("repository_owner"),
            repository_name=data.get("repository_name"),
            analysis_type=data.get("analysis_type", "security"),
            target_files=data.get("target_files", []),
            results=data.get("results", []),
            metadata=data.get("metadata", {})
        )

    def parse_repository_url(self):
        """Parse GitHub repository URL to extract owner and name."""
        if self.repository_url:
            # Handle various GitHub URL formats
            url = self.repository_url.replace("https://github.com/", "")
            url = url.replace(".git", "")
            parts = url.split("/")
            if len(parts) >= 2:
                self.repository_owner = parts[0]
                self.repository_name = parts[1]

    def add_result(self, result: Dict[str, Any]):
        """Add an analysis result."""
        self.results.append(result)

    def get_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        return {
            "repository": f"{self.repository_owner}/{self.repository_name}",
            "analysis_type": self.analysis_type,
            "files_analyzed": len(self.target_files),
            "issues_found": len(self.results),
            "severity_breakdown": self._get_severity_breakdown()
        }

    def _get_severity_breakdown(self) -> Dict[str, int]:
        """Get breakdown of issues by severity."""
        breakdown = {"high": 0, "medium": 0, "low": 0, "info": 0}
        for result in self.results:
            severity = result.get("severity", "info").lower()
            if severity in breakdown:
                breakdown[severity] += 1
        return breakdown


class Config:
    """Configuration management for the agent with LangSmith integration."""

    # Agent Identity (for automatic observability)
    AGENT_NAME: str = "static-code-analysis-agent"
    AGENT_DEMO_NAME: str = "langchain-static-code-analysis-agent-demo"
    AGENT_VERSION: str = "1.0.0"

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4-turbo-preview")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))

    # GitHub Configuration (optional if using MCP)
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")

    # LangSmith Configuration
    LANGSMITH_API_KEY: Optional[str] = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT: str = os.getenv(
        "LANGSMITH_PROJECT",
        "static-code-analysis-agent"
    )
    LANGSMITH_ENDPOINT: str = os.getenv(
        "LANGSMITH_ENDPOINT",
        "https://api.smith.langchain.com"
    )
    LANGSMITH_ENABLED: bool = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"

    # Debug Settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Analysis Settings
    MAX_FILES_PER_ANALYSIS: int = 50
    MAX_FILE_SIZE_KB: int = 500

    # OpenGrep Configuration
    USE_MOCK_OPENGREP: bool = os.getenv("USE_MOCK_OPENGREP", "false").lower() == "true"
    OPENGREP_PATH: str = os.getenv("OPENGREP_PATH", "opengrep")  # Path to opengrep binary
    SECURITY_RULES_PATH: str = "src/rules/security.yaml"
    QUALITY_RULES_PATH: str = "src/rules/quality.yaml"

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return True

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            "model_name": cls.MODEL_NAME,
            "temperature": cls.TEMPERATURE,
            "debug": cls.DEBUG,
            "log_level": cls.LOG_LEVEL,
            "max_files_per_analysis": cls.MAX_FILES_PER_ANALYSIS,
            "max_file_size_kb": cls.MAX_FILE_SIZE_KB,
            "langsmith_enabled": cls.LANGSMITH_ENABLED,
            "langsmith_project": cls.LANGSMITH_PROJECT,
        }


def create_initial_context(repository_url: str, analysis_type: str = "security") -> AnalysisContext:
    """Create initial analysis context."""
    context = AnalysisContext(
        repository_url=repository_url,
        analysis_type=analysis_type
    )
    context.parse_repository_url()
    return context


def create_test_context() -> AnalysisContext:
    """Create a test context for development."""
    return AnalysisContext(
        repository_url="https://github.com/example/test-repo",
        repository_owner="example",
        repository_name="test-repo",
        analysis_type="security",
        metadata={"test_mode": True}
    )
