"""Arize Phoenix observability platform with Nia MCP integration."""

from typing import List, Dict, Any


class PhoenixPlatform:
    """Arize Phoenix platform implementation using dynamic documentation search."""

    @property
    def name(self) -> str:
        """Platform identifier."""
        return "phoenix"

    @property
    def display_name(self) -> str:
        """Human-readable platform name."""
        return "Arize Phoenix"

    def get_dependencies(self) -> List[str]:
        """Returns Phoenix dependencies."""
        return [
            "arize-phoenix>=4.0.0",
            "openinference-instrumentation-langchain>=0.1.0",
        ]

    def get_env_vars(self) -> List[Dict[str, str]]:
        """Returns Phoenix environment variables."""
        return [
            {
                "name": "PHOENIX_COLLECTOR_ENDPOINT",
                "description": "Phoenix collector endpoint URL (optional, defaults to http://localhost:6006)",
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
            prompt = f"""I need to instrument a {framework} {framework_version} codebase with Arize Phoenix observability.

Entry points where agents are instantiated:
{chr(10).join(f"- {ep}" for ep in entry_points)}

Instrumentation targets from config:
{', '.join([t.value for t in config.targets])}

Please follow these steps:

1. **Search Documentation**: Use Nia MCP tools to:
   - Index Phoenix documentation: https://docs.arize.com/phoenix
   - Search for "{framework} instrumentation" or "{framework} OpenInference"
   - Find example code for instrumenting {framework} with Phoenix

2. **Analyze Entry Points**: Use tree-sitter tools to:
   - Parse each entry point file
   - Find agent instantiations
   - Identify exact line numbers for injection

3. **Generate Injection Points**: Based on documentation, create:
   - Import statements (e.g., "from phoenix.trace import using_tracer")
   - Initialization code (e.g., Phoenix session setup)
   - Framework-specific instrumentation calls
   - Tool/function decorators if needed

4. **Return Result**: Provide structured response with injection points, imports, and init code.

Start by searching Phoenix documentation for {framework} integration patterns."""

            response = await agent.run(prompt)

            return {
                "success": True,
                "injection_points": [],
                "imports": [
                    "import phoenix as px",
                    "from phoenix.trace import using_tracer"
                ],
                "init_code": """# Initialize Phoenix
phoenix_session = px.launch_app()
tracer = using_tracer(phoenix_session)
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
        imports = ["import phoenix as px"]
        init_code = ""

        if framework == "langchain":
            imports.extend([
                "from openinference.instrumentation.langchain import LangChainInstrumentor"
            ])
            init_code = """# Initialize Phoenix for LangChain
phoenix_session = px.launch_app()
LangChainInstrumentor().instrument()
"""

        elif framework in ["openai-agents", "openai"]:
            imports.extend(["from openinference.instrumentation.openai import OpenAIInstrumentor"])
            init_code = """# Initialize Phoenix for OpenAI
phoenix_session = px.launch_app()
OpenAIInstrumentor().instrument()
"""

        else:
            init_code = """# Initialize Phoenix
phoenix_session = px.launch_app()
"""

        return {
            "success": False,
            "injection_points": injection_points,
            "imports": imports,
            "init_code": init_code,
            "agent_response": None,
            "error": f"Agent failed, using fallback: {error_msg}"
        }
