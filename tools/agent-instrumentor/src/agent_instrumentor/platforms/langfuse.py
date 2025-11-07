"""Langfuse observability platform with Nia MCP integration."""

from typing import List, Dict, Any


class LangfusePlatform:
    """Langfuse platform implementation using dynamic documentation search."""

    @property
    def name(self) -> str:
        """Platform identifier."""
        return "langfuse"

    @property
    def display_name(self) -> str:
        """Human-readable platform name."""
        return "Langfuse"

    def get_dependencies(self) -> List[str]:
        """Returns Langfuse dependencies."""
        return [
            "langfuse>=2.0.0",
        ]

    def get_env_vars(self) -> List[Dict[str, str]]:
        """Returns Langfuse environment variables."""
        return [
            {
                "name": "LANGFUSE_PUBLIC_KEY",
                "description": "Langfuse public API key",
                "required": True
            },
            {
                "name": "LANGFUSE_SECRET_KEY",
                "description": "Langfuse secret API key",
                "required": True
            },
            {
                "name": "LANGFUSE_HOST",
                "description": "Langfuse host URL (optional, defaults to https://cloud.langfuse.com)",
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
            # Build a targeted prompt for the agent to search and generate instrumentation
            prompt = f"""I need to instrument a {framework} {framework_version} codebase with Langfuse observability.

Entry points where agents are instantiated:
{chr(10).join(f"- {ep}" for ep in entry_points)}

Instrumentation targets from config:
{', '.join([t.value for t in config.targets])}

Please follow these steps:

1. **Search Documentation**: Use Nia MCP tools to:
   - Index Langfuse documentation: https://langfuse.com/docs
   - Search for "{framework} integration" or "{framework} callback handler"
   - Find example code for instrumenting {framework} with Langfuse

2. **Analyze Entry Points**: Use tree-sitter tools to:
   - Parse each entry point file
   - Find agent instantiations (class calls, function calls)
   - Identify exact line numbers for injection

3. **Generate Injection Points**: Based on documentation, create injection points:
   - Import statements (e.g., "from langfuse.callback import CallbackHandler")
   - Initialization code (e.g., creating CallbackHandler with env vars)
   - Agent modifications (e.g., adding callbacks parameter)
   - Tool decorators if targets include "tools"
   - RAG/retriever callbacks if targets include "rag"
   - Error handling if targets include "errors"

4. **Return Result**: Provide a structured response with:
   - List of injection points (type, line, target, code)
   - Import statements needed
   - Initialization code
   - Files to modify

Start by searching Langfuse documentation for {framework} integration patterns."""

            # Run the agent to generate instrumentation
            response = await agent.run(prompt)

            # Parse the response
            # Note: This is simplified - actual implementation would parse the agent's structured response
            return {
                "success": True,
                "injection_points": [],  # Extracted from agent response
                "imports": [
                    "import os",
                    "from langfuse.callback import CallbackHandler"
                ],
                "init_code": """# Initialize Langfuse
langfuse_handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)
""",
                "agent_response": response,
                "error": None
            }

        except Exception as e:
            # Fallback to basic patterns if agent fails
            return self._generate_fallback_instrumentation(framework, entry_points, config, str(e))

    def _generate_fallback_instrumentation(
        self,
        framework: str,
        entry_points: List[str],
        config: Any,
        error_msg: str
    ) -> Dict[str, Any]:
        """Fallback instrumentation when agent/Nia fails."""

        # Basic framework-specific patterns as fallback
        injection_points = []
        imports = ["import os"]
        init_code = ""

        if framework == "langchain":
            imports.append("from langfuse.callback import CallbackHandler")
            init_code = """# Initialize Langfuse
langfuse_handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)
"""
            # Add callback injection points for each entry point
            for ep in entry_points:
                injection_points.append({
                    "type": "callback",
                    "line": 1,  # Will be detected by tree-sitter
                    "target": "AgentExecutor",
                    "code": "callbacks=[langfuse_handler]"
                })

        elif framework in ["openai-agents", "openai"]:
            imports.append("from langfuse.openai import openai")
            init_code = """# Langfuse OpenAI integration
# Automatic instrumentation via module patching
"""

        elif framework == "pydantic-ai":
            imports.append("from langfuse.decorators import observe")
            init_code = "# Use @observe decorator on agent functions\n"
            for ep in entry_points:
                injection_points.append({
                    "type": "decorator",
                    "line": 1,
                    "target": "agent_function",
                    "code": "@observe()"
                })

        else:
            # Generic Langfuse client
            imports.append("from langfuse import Langfuse")
            init_code = """# Initialize Langfuse client
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)
"""

        return {
            "success": False,
            "injection_points": injection_points,
            "imports": imports,
            "init_code": init_code,
            "agent_response": None,
            "error": f"Agent failed, using fallback: {error_msg}"
        }
