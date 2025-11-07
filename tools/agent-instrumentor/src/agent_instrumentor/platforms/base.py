"""Base platform protocol and utilities for observability platforms."""

from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PlatformInfo:
    """Information about an observability platform."""
    name: str
    display_name: str
    dependencies: List[str]
    env_vars: List[Dict[str, str]]
    description: str


class ObservabilityPlatform(Protocol):
    """Protocol for observability platform implementations.

    Each platform must implement these methods to be auto-discovered
    by the platform registry.
    """

    @property
    def name(self) -> str:
        """Unique identifier for the platform (e.g., 'langfuse', 'phoenix')."""
        ...

    @property
    def display_name(self) -> str:
        """Human-readable name for the platform (e.g., 'Langfuse', 'Arize Phoenix')."""
        ...

    def get_dependencies(self) -> List[str]:
        """Return list of Python package dependencies needed for this platform.

        Returns:
            List of package specifications (e.g., ["langfuse>=2.0.0"])
        """
        ...

    def get_env_vars(self) -> List[Dict[str, str]]:
        """Return list of environment variables needed for this platform.

        Returns:
            List of dicts with keys: 'name', 'description', 'required'
            Example:
                [
                    {
                        "name": "LANGFUSE_PUBLIC_KEY",
                        "description": "Langfuse public API key",
                        "required": True
                    }
                ]
        """
        ...

    async def generate_instrumentation(
        self,
        framework: str,
        framework_version: str,
        entry_points: List[str],
        config: Any,
        agent: Any  # Claude agent with MCP tools
    ) -> Dict[str, Any]:
        """Generate instrumentation code for a specific framework.

        This method should use the Claude agent with Nia MCP tools to:
        1. Search for documentation on instrumenting the framework
        2. Generate appropriate instrumentation code
        3. Return injection points for the code generator

        Args:
            framework: Name of the framework (e.g., "langchain")
            framework_version: Version of the framework
            entry_points: List of file paths where agents are instantiated
            config: InstrumentationConfig object
            agent: Claude agent with MCP tools (has access to Nia)

        Returns:
            Dict with:
                - success: bool
                - injection_points: List[Dict] - Where to inject code
                - imports: List[str] - Import statements to add
                - init_code: str - Initialization code
                - error: Optional[str]
        """
        ...

    def get_info(self) -> PlatformInfo:
        """Get platform information."""
        return PlatformInfo(
            name=self.name,
            display_name=self.display_name,
            dependencies=self.get_dependencies(),
            env_vars=self.get_env_vars(),
            description=f"{self.display_name} observability platform"
        )
