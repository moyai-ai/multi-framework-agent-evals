"""DataDog APM observability platform with Nia MCP integration."""

from typing import List, Dict, Any


class DataDogPlatform:
    """DataDog APM platform implementation using dynamic documentation search."""

    @property
    def name(self) -> str:
        """Platform identifier."""
        return "datadog"

    @property
    def display_name(self) -> str:
        """Human-readable platform name."""
        return "DataDog APM"

    def get_dependencies(self) -> List[str]:
        """Returns DataDog dependencies."""
        return [
            "ddtrace>=2.14.0",
        ]

    def get_env_vars(self) -> List[Dict[str, str]]:
        """Returns DataDog environment variables."""
        return [
            {
                "name": "DD_API_KEY",
                "description": "DataDog API key",
                "required": True
            },
            {
                "name": "DD_SITE",
                "description": "DataDog site (e.g., datadoghq.com, datadoghq.eu)",
                "required": False
            },
            {
                "name": "DD_SERVICE",
                "description": "Service name for APM",
                "required": False
            },
            {
                "name": "DD_ENV",
                "description": "Environment name (e.g., production, staging)",
                "required": False
            },
        ]

    async def generate_instrumentation(
        self,
        framework: str,
        framework_version: str,
        entry_points: List[str],
        config: Any,
        agent: Any
    ) -> Dict[str, Any]:
        """Generate instrumentation using Nia MCP to search documentation.

        Args:
            framework: Framework name (e.g., "langchain")
            framework_version: Version string
            entry_points: Files where agents are instantiated
            config: InstrumentationConfig object
            agent: Claude agent with Nia MCP tools

        Returns:
            Dict with injection_points, imports, init_code
        """
        try:
            prompt = f"""I need to instrument a {framework} {framework_version} codebase with DataDog APM.

Entry points where agents are instantiated:
{chr(10).join(f"- {ep}" for ep in entry_points)}

Instrumentation targets from config:
{', '.join([t.value for t in config.targets])}

Please follow these steps:

1. **Search Documentation**: Use Nia MCP tools to:
   - Index DataDog documentation: https://docs.datadoghq.com/tracing/
   - Search for "ddtrace {framework}" or "Python {framework} tracing"
   - Find example code for instrumenting Python {framework} with ddtrace

2. **Analyze Entry Points**: Use tree-sitter tools to:
   - Parse each entry point file
   - Find agent instantiations
   - Identify exact line numbers for injection

3. **Generate Injection Points**: Based on documentation, create:
   - Import statements (e.g., "from ddtrace import tracer, patch")
   - Initialization code (e.g., patch() calls, tracer configuration)
   - Span decorators for functions
   - Context managers for operations

4. **Return Result**: Provide structured response with injection points, imports, and init code.

Start by searching DataDog documentation for {framework} tracing patterns."""

            response = await agent.run(prompt)

            return {
                "success": True,
                "injection_points": [],
                "imports": [
                    "import os",
                    "from ddtrace import tracer, patch"
                ],
                "init_code": """# Initialize DataDog APM
patch(langchain=True)  # Auto-patch supported integrations
tracer.configure(
    hostname=os.getenv("DD_AGENT_HOST", "localhost"),
    port=os.getenv("DD_AGENT_PORT", 8126),
)
""",
                "agent_response": response,
                "error": None
            }

        except Exception as e:
            return self._generate_fallback_instrumentation(framework, entry_points, config, str(e))

    def _generate_fallback_instrumentation(
        self,
        framework: str,
        entry_points: List[str],
        config: Any,
        error_msg: str
    ) -> Dict[str, Any]:
        """Fallback instrumentation when agent/Nia fails."""

        injection_points = []
        imports = ["import os", "from ddtrace import tracer, patch"]
        init_code = ""

        if framework == "langchain":
            init_code = """# Initialize DataDog APM for LangChain
patch(langchain=True)
tracer.configure(
    hostname=os.getenv("DD_AGENT_HOST", "localhost"),
    port=int(os.getenv("DD_AGENT_PORT", "8126")),
)
"""

        elif framework in ["openai-agents", "openai"]:
            init_code = """# Initialize DataDog APM for OpenAI
patch(openai=True)
tracer.configure(
    hostname=os.getenv("DD_AGENT_HOST", "localhost"),
    port=int(os.getenv("DD_AGENT_PORT", "8126")),
)
"""

        else:
            # Generic tracing with manual spans
            imports.append("from ddtrace import tracer")
            init_code = """# Initialize DataDog APM
tracer.configure(
    hostname=os.getenv("DD_AGENT_HOST", "localhost"),
    port=int(os.getenv("DD_AGENT_PORT", "8126")),
)

# Use @tracer.wrap() decorator on functions to trace
"""

        return {
            "success": False,
            "injection_points": injection_points,
            "imports": imports,
            "init_code": init_code,
            "agent_response": None,
            "error": f"Agent failed, using fallback: {error_msg}"
        }
