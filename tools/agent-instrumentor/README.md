# Agent Instrumentor

**Intelligent, autonomous instrumentation of multi-framework agents using ReACT pattern with Nia MCP.**

Agent Instrumentor uses a Claude-powered ReACT agent to automatically detect agent frameworks in your codebase, search documentation for instrumentation patterns, and inject comprehensive observability code.

## 🚀 Features

- **ReACT Agent Pattern**: Reasons about your code, searches documentation, and generates instrumentation intelligently
- **Nia MCP Integration**: Searches PyPI packages, indexes documentation, and finds real-world examples
- **Dynamic Framework Detection**: Auto-discovers any Python agent framework (LangChain, LangGraph, OpenAI, Pydantic AI, CrewAI, Claude SDK, AutoGen, etc.)
- **Multi-Platform Support**: Langfuse, Arize Phoenix, DataDog APM, LangSmith - auto-discovered via platform registry
- **Comprehensive Instrumentation**: Instruments tools, LLM calls, RAG, memory, chains, errors, sub-agents, and prompts
- **Zero Hardcoding**: No static patterns - learns instrumentation from documentation on-the-fly
- **Tree-Sitter AST**: Robust code parsing and injection that handles syntax errors gracefully
- **Configurable**: Granular control over instrumentation scope, cost, and performance impact

## 📋 Requirements

- Python 3.10+
- Anthropic API key (for Claude Agent SDK)
- Nia API key (for documentation search - optional but recommended)

## 🔧 Installation

```bash
# Using uv
cd tools/agent-instrumentor
unset VIRTUAL_ENV && uv sync
```

## Environment Variables

Ensure your `.env` file contains:

```
# Required
ANTHROPIC_API_KEY=your-anthropic-key

# Recommended (for Nia MCP documentation search)
NIA_API_KEY=your-nia-key  # Get one at https://app.trynia.ai/

# Platform-specific (e.g., for Langfuse)
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
```

## 🎯 Quick Start

### Run the Instrumentor

```bash
# Instrument current directory with default settings
unset VIRTUAL_ENV && uv run --env-file .env agent-instrumentor .

# Use a specific platform
unset VIRTUAL_ENV && uv run --env-file .env agent-instrumentor /path/to/codebase --platform phoenix

# Use preset configuration
unset VIRTUAL_ENV && uv run --env-file .env agent-instrumentor /path/to/codebase --preset comprehensive

# Custom targets
unset VIRTUAL_ENV && uv run --env-file .env agent-instrumentor /path/to/codebase --targets tools,llm_calls,rag,memory

# Run from the project root
unset VIRTUAL_ENV && uv run --directory tools/agent-instrumentor --env-file .env agent-instrumentor /path/to/codebase
```

### What Happens

The ReACT agent will:

1. **Detect Frameworks**: Scan your codebase using tree-sitter to find agent frameworks
2. **Search Documentation**: Use Nia MCP to search for instrumentation patterns in official docs
3. **Generate Code**: Create injection points based on learned patterns
4. **Inject Instrumentation**: Modify your code with observability instrumentation
5. **Validate**: Ensure generated code is syntactically correct with black formatting

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ReACT Agent                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  System Prompt: Expert instrumentation specialist    │  │
│  │  - Detects frameworks                                 │  │
│  │  - Searches documentation                             │  │
│  │  - Reasons about injection points                     │  │
│  │  - Generates instrumentation code                     │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│       ┌──────────────────┴──────────────────┐               │
│       ▼                                     ▼               │
│  ┌─────────────┐                     ┌────────────────┐    │
│  │  Nia MCP    │                     │  In-Process    │    │
│  │  (External) │                     │  Tools (SDK)   │    │
│  ├─────────────┤                     ├────────────────┤    │
│  │ • Search    │                     │ • Tree-sitter  │    │
│  │   packages  │                     │   parser       │    │
│  │ • Index     │                     │ • Framework    │    │
│  │   docs      │                     │   detector     │    │
│  │ • Query     │                     │ • Code         │    │
│  │   indexed   │                     │   generator    │    │
│  │   content   │                     │ • Package      │    │
│  └─────────────┘                     │   analyzer     │    │
│                                      └────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
    ┌───────────────┐          ┌──────────────────┐
    │   Platform    │          │  Instrumented    │
    │   Registry    │          │  Codebase        │
    ├───────────────┤          └──────────────────┘
    │ • Langfuse    │
    │ • Phoenix     │
    │ • DataDog     │
    │ • LangSmith   │
    └───────────────┘
```

### Key Components

#### 1. ReACT Agent (`agents/react_instrumentor.py`)
- **Model**: Claude Sonnet 4
- **Pattern**: Reason → Act → Observe loop
- **Tools**: Nia MCP (external) + Instrumentor Tools (in-process)
- **Workflow**:
  1. Observe: Detect frameworks
  2. Think: "Need to learn instrumentation for LangChain 0.3.1"
  3. Act: Search Nia MCP for docs
  4. Observe: Found callback handler pattern
  5. Think: "Need to inject at line 45"
  6. Act: Generate and inject code

#### 2. Nia MCP Integration
- **Connection**: External stdio server via `uvx nia-mcp-server`
- **Tools Available**:
  - `nia_search_package`: Search PyPI packages for patterns
  - `nia_index_documentation`: Index framework docs
  - `nia_search_documentation`: Query indexed docs
  - `nia_read_package_file`: Read files from packages
- **Benefit**: Learns instrumentation patterns from official sources

#### 3. In-Process Tools (Tree-Sitter)
- **Parser**: Robust Python AST using tree-sitter
- **Tools**:
  - `detect_frameworks`: Find agent frameworks in codebase
  - `parse_python_file`: Parse files into AST
  - `find_imports/functions/classes/calls`: Query AST
  - `inject_instrumentation_code`: Modify code with tree-sitter
  - `extract_package_versions`: Get versions from requirements

#### 4. Platform Registry (`platforms/registry.py`)
- **Auto-Discovery**: Scans `platforms/` directory at runtime
- **No Hardcoding**: Platforms implement `ObservabilityPlatform` protocol
- **Dynamic**: Add new platforms by dropping files in `platforms/`
- **Current Platforms**:
  - Langfuse (`langfuse.py`)
  - Arize Phoenix (`phoenix.py`)
  - DataDog APM (`datadog.py`)
  - LangSmith (`langsmith.py`)

## 📖 Usage Examples

### List Available Platforms

```bash
unset VIRTUAL_ENV && uv run --env-file .env agent-instrumentor --list-platforms
```

Output:
```
📊 Available Observability Platforms:

  • Langfuse (langfuse)
    Dependencies: langfuse>=2.0.0
    Environment Variables:
      - LANGFUSE_PUBLIC_KEY (required)
      - LANGFUSE_SECRET_KEY (required)
      - LANGFUSE_HOST (optional)

  • Arize Phoenix (phoenix)
    Dependencies: arize-phoenix>=4.0.0, openinference-instrumentation-langchain>=0.1.0
    Environment Variables:
      - PHOENIX_COLLECTOR_ENDPOINT (optional)

  • DataDog APM (datadog)
    Dependencies: ddtrace>=2.14.0
    Environment Variables:
      - DD_API_KEY (required)
      - DD_SITE (optional)
      - DD_SERVICE (optional)
      - DD_ENV (optional)

  • LangSmith (langsmith)
    Dependencies: langsmith>=0.1.0
    Environment Variables:
      - LANGCHAIN_API_KEY (required)
      - LANGCHAIN_TRACING_V2 (required)
      - LANGCHAIN_PROJECT (optional)
```

### Preset Configurations

#### Minimal (Low Cost/Overhead)
```bash
unset VIRTUAL_ENV && uv run --env-file .env agent-instrumentor . --preset minimal
```
- Targets: LLM calls only
- Use case: Basic usage tracking

#### Standard (Balanced)
```bash
unset VIRTUAL_ENV && uv run --env-file .env agent-instrumentor . --preset standard
```
- Targets: Tools, LLM calls, chains, errors
- Use case: Production monitoring

#### Comprehensive (Full Observability)
```bash
unset VIRTUAL_ENV && uv run --env-file .env agent-instrumentor . --preset comprehensive
```
- Targets: All components (tools, LLM, RAG, memory, chains, errors, sub-agents, prompts)
- Use case: Deep debugging and optimization

### Custom Configuration

```bash
unset VIRTUAL_ENV && uv run --env-file .env agent-instrumentor /path/to/codebase \
  --platform phoenix \
  --level comprehensive \
  --targets tools,llm_calls,rag \
  --cost-limit high \
  --performance-impact detailed
```

## 🔍 How It Works: Example Walkthrough

### Input: LangChain Codebase

```python
# agents.py
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent

llm = ChatOpenAI(model="gpt-4")
agent_executor = AgentExecutor(
    agent=create_react_agent(llm, tools, prompt),
    tools=tools,
    verbose=True
)
```

### Agent Execution

```
🚀 Starting ReACT agent...

[Agent] Observe: Calling detect_frameworks tool...
[Tool] Detected: langchain 0.3.1 in agents.py

[Agent] Think: Found LangChain 0.3.1. Need to learn Langfuse instrumentation.

[Agent] Act: Indexing Langfuse documentation...
[Nia MCP] Indexed: https://langfuse.com/docs

[Agent] Act: Searching for "LangChain callback handler"...
[Nia MCP] Found: CallbackHandler pattern in docs

[Agent] Observe: Pattern requires:
  - Import: from langfuse.callback import CallbackHandler
  - Init: Create handler with env vars
  - Inject: Add callbacks=[handler] to AgentExecutor

[Agent] Act: Parsing agents.py with tree-sitter...
[Tool] Found AgentExecutor at line 45

[Agent] Think: Need to inject callback parameter at line 45

[Agent] Act: Generating injection points...
[Agent] Act: Injecting code...
[Tool] Code validated and formatted with black

✅ Instrumentation completed!
```

### Output: Instrumented Code

```python
# agents.py
import os
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langfuse.callback import CallbackHandler

# Initialize Langfuse
langfuse_handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

llm = ChatOpenAI(model="gpt-4")
agent_executor = AgentExecutor(
    agent=create_react_agent(llm, tools, prompt),
    tools=tools,
    verbose=True,
    callbacks=[langfuse_handler]  # ← Injected by agent
)
```

## 🛠️ Configuration

### InstrumentationConfig Schema

```python
from agent_instrumentor.config import InstrumentationConfig, InstrumentationLevel, InstrumentationTarget

config = InstrumentationConfig(
    level=InstrumentationLevel.STANDARD,
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
    cost_limit="medium",  # low, medium, high
    performance_impact="acceptable",  # minimal, acceptable, detailed
    frameworks=[],  # Empty = all detected
    exclude_patterns=["**/test_*.py", "**/tests/**"]
)
```

## 🧩 Adding a New Platform

Create a new file in `platforms/` that implements the `ObservabilityPlatform` protocol:

```python
# platforms/my_platform.py
from typing import List, Dict, Any

class MyPlatform:
    @property
    def name(self) -> str:
        return "myplatform"

    @property
    def display_name(self) -> str:
        return "My Platform"

    def get_dependencies(self) -> List[str]:
        return ["myplatform>=1.0.0"]

    def get_env_vars(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "MY_PLATFORM_API_KEY",
                "description": "API key for My Platform",
                "required": True
            }
        ]

    async def generate_instrumentation(
        self,
        framework: str,
        framework_version: str,
        entry_points: List[str],
        config: Any,
        agent: Any
    ) -> Dict[str, Any]:
        # Use the agent to search for instrumentation patterns
        prompt = f"Search for {framework} instrumentation with My Platform"
        response = await agent.run(prompt)

        return {
            "success": True,
            "injection_points": [...],
            "imports": [...],
            "init_code": "...",
            "agent_response": response
        }
```

That's it! The platform will be auto-discovered on next run.

## 📂 Project Structure

```
agent-instrumentor/
├── src/agent_instrumentor/
│   ├── main.py                  # CLI with argparse
│   ├── agents/
│   │   ├── react_instrumentor.py  # ReACT agent
│   │   └── prompts.py           # System prompts
│   ├── tools/                   # In-process MCP tools
│   │   ├── tree_sitter_parser.py
│   │   ├── framework_detector.py
│   │   ├── code_generator.py
│   │   └── package_analyzer.py
│   ├── platforms/               # Auto-discovered platforms
│   │   ├── base.py              # Platform protocol
│   │   ├── registry.py          # Auto-discovery
│   │   ├── langfuse.py
│   │   ├── phoenix.py
│   │   ├── datadog.py
│   │   └── langsmith.py
│   ├── config/
│   │   ├── schema.py            # Config models
│   │   └── presets.py           # Standard configs
│   └── cache/                   # Cached patterns
├── pyproject.toml
├── .env                         # API keys and environment variables
└── README.md
```

## 🔬 Testing

```bash
# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Lint
uv run ruff check src/
```

## 🐛 Troubleshooting

### "NIA_API_KEY not set"

Ensure your `.env` file contains `NIA_API_KEY=your-key`. Get a free key at https://app.trynia.ai/. Without it, the agent will use fallback patterns instead of learning from docs.

### "No frameworks detected"

Ensure your codebase has Python files importing agent frameworks. Check the detection patterns in `tools/framework_detector.py`.

### "Agent failed"

Each platform has fallback instrumentation when the agent fails. Check the error message and ensure your `.env` file contains valid API keys.

## 📚 Learn More

- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
- [Nia MCP](https://docs.trynia.ai/integrations/nia-mcp)
- [Tree-Sitter Python](https://github.com/tree-sitter/py-tree-sitter)
- [Langfuse](https://langfuse.com/docs)
- [Arize Phoenix](https://docs.arize.com/phoenix)

## 🤝 Contributing

Contributions welcome! Areas of interest:

- New platform implementations
- Enhanced framework detection patterns
- Improved ReACT prompts
- Additional instrumentation targets
- Performance optimizations

## 📝 License

MIT

## 🙏 Acknowledgments

Built with:
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) by Anthropic
- [Nia MCP](https://trynia.ai) for intelligent documentation search
- [Tree-Sitter](https://tree-sitter.github.io/) for robust code parsing
