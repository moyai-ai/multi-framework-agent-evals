"""LangSmith observability platform with Nia MCP integration."""

from typing import List, Dict, Any


class LangSmithPlatform:
    """LangSmith platform implementation using dynamic documentation search."""

    @property
    def name(self) -> str:
        """Platform identifier."""
        return "langsmith"

    @property
    def display_name(self) -> str:
        """Human-readable platform name."""
        return "LangSmith"

    def get_dependencies(self) -> List[str]:
        """Returns LangSmith dependencies."""
        return [
            "langsmith>=0.1.0",
        ]

    def get_env_vars(self) -> List[Dict[str, str]]:
        """Returns LangSmith environment variables."""
        return [
            {
                "name": "LANGCHAIN_API_KEY",
                "description": "LangSmith API key",
                "required": True
            },
            {
                "name": "LANGCHAIN_TRACING_V2",
                "description": "Enable LangSmith tracing (set to 'true')",
                "required": True
            },
            {
                "name": "LANGCHAIN_PROJECT",
                "description": "LangSmith project name",
                "required": False
            },
            {
                "name": "LANGCHAIN_ENDPOINT",
                "description": "LangSmith API endpoint (optional, defaults to https://api.smith.langchain.com)",
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
            prompt = f"""I need to instrument a {framework} {framework_version} codebase with LangSmith observability.

Entry points where agents are instantiated:
{chr(10).join(f"- {ep}" for ep in entry_points)}

Instrumentation targets from config:
{', '.join([t.value for t in config.targets])}

Please follow these steps:

1. **Search Documentation**: Use Nia MCP tools to:
   - Index LangSmith documentation: https://docs.smith.langchain.com
   - Search for "{framework} tracing" or "{framework} LangSmith integration"
   - Find example code for instrumenting {framework} with LangSmith

2. **Analyze Entry Points**: Use tree-sitter tools to:
   - Parse each entry point file
   - Find agent instantiations
   - Identify exact line numbers for injection

3. **Generate Injection Points**: Based on documentation, create:
   - Import statements (e.g., "from langsmith import Client")
   - Initialization code (e.g., Client setup, environment variables)
   - Callback handlers if applicable
   - Tracing decorators

4. **Return Result**: Provide structured response with injection points, imports, and init code.

Start by searching LangSmith documentation for {framework} integration patterns."""

            response = await agent.run(prompt)

            return {
                "success": True,
                "injection_points": [],
                "imports": [
                    "import os",
                    "from langsmith import Client"
                ],
                "init_code": """# Initialize LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "default")

langsmith_client = Client()
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
        imports = ["import os"]
        init_code = ""

        if framework == "langchain":
            imports.extend(["from langsmith import Client"])
            init_code = """# Initialize LangSmith for LangChain
# LangChain has built-in LangSmith integration via environment variables
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "default")

# Automatic tracing is enabled via environment variables
# No code changes needed in LangChain agents!
"""

        elif framework == "langgraph":
            imports.extend(["from langsmith import Client"])
            init_code = """# Initialize LangSmith for LangGraph
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "default")

# LangGraph inherits LangChain's automatic tracing
"""

        else:
            # Generic tracing with Client
            imports.extend(["from langsmith import Client", "from langsmith import traceable"])
            init_code = """# Initialize LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

langsmith_client = Client()

# Use @traceable decorator on functions to trace:
# from langsmith import traceable
# @traceable
# def my_function():
#     ...
"""

        return {
            "success": False,
            "injection_points": injection_points,
            "imports": imports,
            "init_code": init_code,
            "agent_response": None,
            "error": f"Agent failed, using fallback: {error_msg}"
        }
