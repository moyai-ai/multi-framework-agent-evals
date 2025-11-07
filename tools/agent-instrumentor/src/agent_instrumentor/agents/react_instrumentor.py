"""ReACT agent for intelligent code instrumentation."""

import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    from claude_agent_sdk import (
        query,
        ClaudeAgentOptions,
        AssistantMessage,
        TextBlock,
        ToolUseBlock,
        ResultMessage,
    )
except ImportError:
    raise ImportError(
        "claude-agent-sdk is required. Install with: pip install claude-agent-sdk"
    )

try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None  # type: ignore

from ..tools import (
    parse_python_file,
    find_imports,
    find_function_definitions,
    find_class_definitions,
    find_function_calls,
    detect_frameworks,
    get_framework_details,
    inject_instrumentation_code,
    write_instrumented_file,
    extract_package_versions,
    get_framework_version,
)
from ..config import InstrumentationConfig
from ..platforms import get_platform
from .prompts import REACT_INSTRUMENTOR_PROMPT


# Tool execution handler for custom instrumentation tools
TOOL_HANDLERS = {
    "parse_python_file": parse_python_file,
    "find_imports": find_imports,
    "find_function_definitions": find_function_definitions,
    "find_class_definitions": find_class_definitions,
    "find_function_calls": find_function_calls,
    "detect_frameworks": detect_frameworks,
    "get_framework_details": get_framework_details,
    "inject_instrumentation_code": inject_instrumentation_code,
    "write_instrumented_file": write_instrumented_file,
    "extract_package_versions": extract_package_versions,
    "get_framework_version": get_framework_version,
}


def initialize_langfuse() -> Optional[Langfuse]:
    """Initialize Langfuse client if credentials are available.

    Returns:
        Langfuse client or None if not configured
    """
    if not LANGFUSE_AVAILABLE:
        return None

    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    if not secret_key or not public_key:
        print("⚠️  Langfuse credentials not found. Set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY to enable tracing.")
        return None

    try:
        langfuse_client = Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=base_url,
        )
        print(f"✅ Langfuse initialized: {base_url}")
        return langfuse_client
    except Exception as e:
        print(f"⚠️  Failed to initialize Langfuse: {e}")
        return None


async def execute_tool(tool_name: str, args: Dict[str, Any]) -> Any:
    """Execute a custom instrumentation tool.
    
    Args:
        tool_name: Name of the tool to execute
        args: Arguments for the tool
        
    Returns:
        Tool execution result
    """
    if tool_name not in TOOL_HANDLERS:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    handler = TOOL_HANDLERS[tool_name]
    
    # Handle async and sync handlers
    if asyncio.iscoroutinefunction(handler):
        return await handler(args)
    else:
        return handler(args)


def create_agent_options(
    codebase_path: str,
    config: InstrumentationConfig,
) -> ClaudeAgentOptions:
    """Create agent options for code instrumentation.

    Args:
        codebase_path: Path to the codebase to instrument
        config: Instrumentation configuration

    Returns:
        ClaudeAgentOptions configured for instrumentation
    """
    # Use built-in SDK tools for file operations
    # The agent will use Read/Write tools to interact with files
    # Custom tool execution will be handled manually
    allowed_tools = [
        "Read",
        "Write",
        "Edit",
        "Grep",
        "Glob",
        "TodoWrite",
        # Nia MCP Documentation Tools (format: mcp__[server-name]__[tool-name])
        "mcp__nia__index_documentation",        # Index docs sites
        "mcp__nia__search_documentation",       # Search indexed docs
        "mcp__nia__nia_package_search_grep",    # Search PyPI packages
        "mcp__nia__nia_package_search_hybrid",  # AI-powered package search
        "mcp__nia__nia_web_search",             # Web search for docs/repos
    ]

    # Create enhanced system prompt with context
    platform = get_platform(config.platform)
    platform_name = platform.display_name if platform else config.platform

    enhanced_prompt = f"""{REACT_INSTRUMENTOR_PROMPT}

## Current Task Context

- **Codebase**: {codebase_path}
- **Platform**: {platform_name}
- **Instrumentation Level**: {config.level.value}
- **Targets**: {', '.join([t.value for t in config.targets])}

## Available Tools

### Built-in File Operations:
- **Read**: Read files from the codebase
- **Write**: Write new files to the codebase
- **Edit**: Edit existing files in the codebase
- **Grep**: Search for patterns in files
- **Glob**: Find files matching patterns
- **TodoWrite**: Create todo items to track your progress

### Nia MCP Documentation Tools:
- **mcp__nia__index_documentation**: Index platform documentation sites (e.g., https://langfuse.com/docs)
- **mcp__nia__search_documentation**: Query indexed documentation with natural language
- **mcp__nia__nia_package_search_grep**: Search PyPI packages for code patterns using regex
- **mcp__nia__nia_package_search_hybrid**: AI-powered semantic search across packages
- **mcp__nia__nia_web_search**: Discover documentation and repositories on the web

## Recommended Workflow

1. **Detect frameworks**: Use Grep/Glob to find framework imports and usage
2. **Index documentation**: Use mcp__nia__index_documentation to index the platform's docs
3. **Search for patterns**: Use mcp__nia__search_documentation to find instrumentation examples
4. **Search packages**: Use mcp__nia__nia_package_search_grep to find code in PyPI packages
5. **Generate code**: Use Edit to add instrumentation code to files

Example:
1. Index Langfuse docs: `mcp__nia__index_documentation(url="https://langfuse.com/docs")`
2. Search: `mcp__nia__search_documentation(query="How to add LangChain CallbackHandler")`
3. Apply: Use Edit tool to add the instrumentation code

Begin by detecting the frameworks in the codebase, then use Nia MCP tools to search for accurate, up-to-date instrumentation patterns.
"""

    # Create agent options with system prompt and MCP server configuration
    options = ClaudeAgentOptions(
        allowed_tools=allowed_tools,
        cwd=codebase_path,
        max_turns=50,  # Allow multiple turns for complex instrumentation
        system_prompt=enhanced_prompt,
        mcp_servers={
            "nia": {
                "type": "stdio",  # External MCP server via stdio
                "command": "uvx",
                "args": ["nia-mcp-server"],
                "env": {
                    "NIA_API_KEY": os.getenv("NIA_API_KEY", ""),
                    "NIA_API_URL": os.getenv("NIA_API_URL", "https://apigcp.trynia.ai/")
                }
            }
        }
    )

    return options


async def instrument_codebase_with_agent(
    codebase_path: str,
    config: InstrumentationConfig,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Instrument a codebase using the ReACT agent.

    Args:
        codebase_path: Path to the codebase to instrument
        config: Instrumentation configuration
        api_key: Anthropic API key (optional, defaults to ANTHROPIC_API_KEY env var)

    Returns:
        Dict with instrumentation results:
            - success: bool
            - frameworks_detected: List[str]
            - files_modified: List[str]
            - report: str
            - error: Optional[str]
    """
    # Initialize Langfuse for self-instrumentation
    langfuse_client = initialize_langfuse()

    try:
        # Create agent options (includes system prompt)
        options = create_agent_options(codebase_path, config)

        # Initial prompt for the agent
        initial_prompt = f"""Please instrument the codebase at {codebase_path} with {config.platform} observability.

Configuration:
- Level: {config.level.value}
- Targets: {', '.join([t.value for t in config.targets])}

Start by detecting the frameworks using Grep and Read tools, then proceed with instrumentation."""

        # Collect all messages and responses
        messages: List[Dict[str, Any]] = []
        text_responses: List[str] = []
        tools_used: List[str] = []
        frameworks_detected: List[str] = []
        files_modified: List[str] = []
        turn_count = 0

        # Use Langfuse context manager for tracing
        if langfuse_client:
            with langfuse_client.start_as_current_span(
                name="agent_instrumentor_execution",
                input={
                    "codebase_path": codebase_path,
                    "platform": config.platform,
                    "level": config.level.value,
                    "targets": [t.value for t in config.targets],
                    "prompt": initial_prompt,
                },
                metadata={
                    "max_turns": options.max_turns,
                    "cwd": options.cwd,
                },
            ) as trace_span:
                # Create generation span for the agent execution
                with trace_span.start_as_current_generation(
                    name="agent_query_execution",
                    model="claude-3-5-sonnet-20241022",
                    input=initial_prompt,
                ) as generation_span:
                    # Query the agent
                    async for message in query(
                        prompt=initial_prompt,
                        options=options,
                    ):
                        if isinstance(message, AssistantMessage):
                            turn_count += 1
                            message_data = {"type": "assistant", "content": [], "turn": turn_count}

                            for block in message.content:
                                if isinstance(block, TextBlock):
                                    text_responses.append(block.text)
                                    message_data["content"].append({
                                        "type": "text",
                                        "text": block.text
                                    })
                                elif isinstance(block, ToolUseBlock):
                                    tools_used.append(block.name)
                                    message_data["content"].append({
                                        "type": "tool_use",
                                        "name": block.name,
                                        "input": block.input
                                    })

                                    # Log tool call to Langfuse as span
                                    tool_span = trace_span.start_span(
                                        name=f"tool_{block.name}",
                                        input=block.input,
                                        metadata={
                                            "tool_name": block.name,
                                            "turn": turn_count,
                                        },
                                    )
                                    tool_span.end()

                                    # Track file modifications
                                    if block.name in ["Write", "Edit"]:
                                        file_path = block.input.get("file_path", block.input.get("path", ""))
                                        if file_path:
                                            files_modified.append(file_path)

                            messages.append(message_data)

                        elif isinstance(message, ResultMessage):
                            # Store result metadata
                            result_data = {
                                "type": "result",
                                "usage": message.usage,
                                "total_cost_usd": message.total_cost_usd,
                            }
                            messages.append(result_data)

                            # Update generation span with usage
                            if hasattr(message, 'usage') and message.usage:
                                generation_span.update(
                                    output="\n\n".join(text_responses),
                                    usage_details={
                                        "input": message.usage.get("input_tokens", 0),
                                        "output": message.usage.get("output_tokens", 0),
                                        "total": message.usage.get("input_tokens", 0) + message.usage.get("output_tokens", 0),
                                    },
                                    cost_details={
                                        "total_cost": message.total_cost_usd,
                                    } if message.total_cost_usd else None,
                                    metadata={
                                        "total_turns": turn_count,
                                    }
                                )
        else:
            # No Langfuse - run without instrumentation
            async for message in query(
                prompt=initial_prompt,
                options=options,
            ):
                if isinstance(message, AssistantMessage):
                    turn_count += 1
                    message_data = {"type": "assistant", "content": [], "turn": turn_count}

                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text_responses.append(block.text)
                            message_data["content"].append({
                                "type": "text",
                                "text": block.text
                            })
                        elif isinstance(block, ToolUseBlock):
                            tools_used.append(block.name)
                            message_data["content"].append({
                                "type": "tool_use",
                                "name": block.name,
                                "input": block.input
                            })

                            # Track file modifications
                            if block.name in ["Write", "Edit"]:
                                file_path = block.input.get("file_path", block.input.get("path", ""))
                                if file_path:
                                    files_modified.append(file_path)

                    messages.append(message_data)

                elif isinstance(message, ResultMessage):
                    # Store result metadata
                    result_data = {
                        "type": "result",
                        "usage": message.usage,
                        "total_cost_usd": message.total_cost_usd,
                    }
                    messages.append(result_data)

        # Extract frameworks from responses (simplified - could be improved)
        # Look for framework mentions in text responses
        framework_keywords = [
            "langchain", "langgraph", "openai", "crewai", "pydantic-ai",
            "google-adk", "claude-agent-sdk", "autogen"
        ]
        for response in text_responses:
            for keyword in framework_keywords:
                if keyword.lower() in response.lower() and keyword not in frameworks_detected:
                    frameworks_detected.append(keyword)

        # Compile the report
        report = {
            "prompt": initial_prompt,
            "codebase_path": codebase_path,
            "platform": config.platform,
            "timestamp": datetime.now().isoformat(),
            "tools_used": list(set(tools_used)),
            "messages": messages,
            "summary": "\n\n".join(text_responses),
        }

        result = {
            "success": True,
            "frameworks_detected": frameworks_detected,
            "files_modified": list(set(files_modified)),
            "report": json.dumps(report, indent=2),
            "error": None
        }

        # Flush Langfuse to ensure all events are sent
        if langfuse_client:
            langfuse_client.flush()

        return result

    except Exception as e:
        error_result = {
            "success": False,
            "frameworks_detected": [],
            "files_modified": [],
            "report": None,
            "error": str(e)
        }

        # Flush Langfuse to ensure error is logged
        if langfuse_client:
            langfuse_client.flush()

        return error_result
