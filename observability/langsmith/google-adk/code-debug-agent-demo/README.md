# Code Debug Agent Demo with LangSmith Observability

A Google Agent Development Kit (ADK) debugging agent with comprehensive LangSmith observability. This agent searches Stack Exchange to help developers debug code errors, with full tracing of agent execution, tool calls, and LLM generations.

## Features

- **Error-Specific Search**: Intelligent keyword extraction from error messages
- **Multi-Source Results**: Stack Overflow, ServerFault, and other Stack Exchange sites
- **Solution Ranking**: Prioritizes accepted answers and high-vote solutions
- **Framework-Aware**: Filters by programming language and framework
- **LangSmith Observability**: Full tracing of agent workflows, tool calls, and RAG operations

## Architecture

### Key Components

- **`src/tools.py`**: Stack Exchange search tools with `@traceable` decorators for automatic tracing
- **`src/agents.py`**: Google ADK agent definitions with traced callbacks
- **`src/traced_runner.py`**: Advanced runner wrapper for custom tracing scenarios
- **`src/services/stackexchange_service.py`**: Context provider for RAG operations
- **`src/runner.py`**: Standard scenario runner with optional `--traced` flag

### What Gets Traced

When running with `--traced` flag, LangSmith captures:

1. **Agent Execution**: Complete workflow including decision-making process
2. **Tool Calls**: All Stack Exchange searches (RAG/context provider operations)
3. **LLM Generations**: Gemini model invocations with token usage and latency
4. **Callbacks**: Response formatting and post-processing operations
5. **Errors**: Full exception traces with context

## Prerequisites

- Python 3.11+
- LangSmith account and API key ([sign up](https://smith.langchain.com))
- Google Gemini API key ([get key](https://aistudio.google.com/app/apikey))
- Stack Exchange API key (optional, for higher rate limits)

## Installation

```bash
# Install dependencies
pip install -e .

# Or with uv
uv sync
```

## Configuration

Create a `.env` file (see `.env.example`):

```env
# LangSmith Configuration
LANGSMITH_API_KEY=ls_your_api_key_here
LANGSMITH_PROJECT=code-debug-agent
LANGSMITH_TRACING=true

# Google Gemini Configuration (using direct API, not Vertex AI)
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_MODEL=gemini-2.0-flash
GOOGLE_GENAI_USE_VERTEXAI=0

# Stack Exchange (optional)
STACKEXCHANGE_API_KEY=your_stackexchange_key_here
```

**Get API Keys:**
- **LangSmith**: https://smith.langchain.com/settings
- **Google Gemini**: https://aistudio.google.com/app/apikey
- **Stack Exchange**: https://stackapps.com/apps/oauth/register

## Usage

### Running Scenarios with Tracing

The recommended way to run scenarios with LangSmith observability is using the `--traced` flag:

```bash
# Run all scenarios with LangSmith tracing (recommended with uv)
unset VIRTUAL_ENV && uv run python -m src.runner --all-scenarios --traced

# Run with specific agent
unset VIRTUAL_ENV && uv run python -m src.runner --all-scenarios --traced quick_debug_agent

# Run specific scenario file
unset VIRTUAL_ENV && uv run python -m src.runner src/scenarios/python_import_error_missing_module.json --traced

# Run specific scenario with specific agent
unset VIRTUAL_ENV && uv run python -m src.runner src/scenarios/javascript_type_error_undefined_property.json --traced debug_agent
```

**What the `--traced` flag does:**
- Creates a LangSmith trace for each scenario execution
- Automatically traces all tool calls via `@traceable` decorators
- Captures LLM generations, agent workflows, and errors
- Groups traces by scenario name for easy analysis in LangSmith dashboard

### Running Without Tracing

Omit the `--traced` flag to run scenarios without LangSmith observability:

```bash
# Run all scenarios (no tracing)
unset VIRTUAL_ENV && uv run python -m src.runner --all-scenarios

# Run specific scenario (no tracing)
python -m src.runner src/scenarios/sample_python_import_error.json
```

### Advanced: Using TracedAgentRunner Directly

For custom use cases, use `src/traced_runner.py` directly:

```python
import asyncio
from src.traced_runner import run_debug_agent_traced

async def main():
    response = await run_debug_agent_traced(
        prompt="ImportError: No module named 'pandas'",
        agent_name="debug_agent",
        user_id="developer_123",
        session_id="debug_session_001"
    )
    print(response)

asyncio.run(main())
```

Or with the `TracedAgentRunner` class:

```python
import asyncio
from src.traced_runner import TracedAgentRunner

async def main():
    runner = TracedAgentRunner(agent_name="debug_agent")

    async for event in runner.run_traced(
        prompt="TypeError: Cannot read property 'map' of undefined",
        user_id="dev_456",
        session_id="session_002"
    ):
        print(f"Event: {event}")

asyncio.run(main())
```

## Available Agents

### `debug_agent` (Default)
Full-featured debugging agent with all tools:
- Comprehensive error analysis
- Multiple search strategies
- Detailed Stack Exchange integration
- Response formatting

### `quick_debug_agent`
Fast, focused debugging agent:
- Limited to essential tools
- Optimized for quick responses
- Best for simple errors

### `sequential_debug_agent`
Multi-step debugging workflow:
- Error analysis agent (first step)
- Solution finder agent (second step)
- Demonstrates sub-agent tracing

## Testing

### Running Tests

Verify that LangSmith tracing didn't break any functionality:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_agents.py -v

# Run tests with verbose output
pytest tests/ -v
```

### Expected Test Results

All tests should pass whether tracing is enabled or not. The test suite verifies:
- Agent initialization and configuration
- Tool function execution
- Scenario loading and execution
- Error handling
- Agent selection logic

**Important**: Tests verify core functionality. To verify that tracing works correctly, run scenarios with `--traced` flag and check the LangSmith dashboard.

### Verifying Tracing Works

1. **Run a scenario with tracing:**
   ```bash
   unset VIRTUAL_ENV && uv run python -m src.runner src/scenarios/python_import_error_missing_module.json --traced
   ```

2. **Check the LangSmith dashboard:**
   - Navigate to https://smith.langchain.com
   - Select your project (e.g., "code-debug-agent")
   - Verify traces appear for the scenario execution
   - Inspect trace to see tool calls, LLM generations, and timing

3. **Expected trace structure:**
   ```
   Scenario: Python Import Error Missing Module
   ├── debug_agent_execution
   │   ├── search_stack_exchange_for_error (tool)
   │   ├── format_debug_response (callback)
   │   └── Gemini LLM generation
   └── Response assembly
   ```

## Viewing Traces in LangSmith

After running scenarios with `--traced`, view comprehensive traces at https://smith.langchain.com:

1. **Navigate to your project** (e.g., "code-debug-agent")
2. **View traces** organized by:
   - Scenario name
   - Agent type (debug_agent, quick_debug_agent, etc.)
   - Timestamp and session ID

**Each trace shows:**
- Full agent execution flow
- Tool call hierarchy (Stack Exchange searches)
- Context provider/RAG operations with results
- LLM token usage, latency, and model parameters
- Error stack traces with full context (if any)
- Input/output for each step

## Scenarios

Pre-configured scenarios are available in `src/scenarios/`:

- `python_import_error_missing_module.json`
- `javascript_type_error_undefined_property.json`
- `typescript_type_error.json`
- `react_hook_rules_violation.json`
- `django_migration_error.json`
- `nodejs_module_resolution_error.json`
- And more...

Each scenario tests different error types and programming languages.

## LangSmith Integration Details

### Important Implementation Note

**LangSmith `@traceable` decorators are NOT applied directly to tool functions and callbacks** because they interfere with Google ADK's function signature parsing (the decorator adds a `config` parameter that breaks ADK's automatic function calling).

Instead, tracing is handled at the **runner level**:
- `src/runner.py`: Scenario-level tracing via `--traced` flag
- `src/traced_runner.py`: Advanced tracing wrapper for custom use cases

### Scenario-Level Tracing

When using `--traced` flag, each scenario execution creates a top-level trace in LangSmith that automatically captures:
- All tool calls (Stack Exchange searches)
- LLM generations (Gemini API calls)
- Agent decision-making and responses
- Execution time and errors

Example trace hierarchy:
```
Scenario: Python Import Error
├── Agent initialization
├── Tool call: search_stack_exchange_for_error
│   └── Stack Exchange API request
├── LLM generation (Gemini)
└── Response formatting
```

### Implementation Pattern

**Tools** (`src/tools.py`):
```python
# NO decorator - allows Google ADK to parse function signatures correctly
async def search_stack_exchange_for_error(
    error_message: str,
    programming_language: Optional[str],
    framework: Optional[str],
    include_solutions: bool,
    max_results: int
) -> str:
    """Search Stack Exchange for solutions."""
    # Tool implementation - traced at runner level
```

**Callbacks** (`src/agents.py`):
```python
# NO decorator - same reasoning as tools
def _format_debug_response(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse:
    """Format responses."""
    # Callback implementation - traced at runner level
```

**Runner** (`src/runner.py`):
```python
# Tracing applied here when --traced flag is used
@traceable(name=f"Scenario: {scenario.name}")
async def execute_traced():
    return await self._run_scenario_untraced(scenario)
```

## Project Structure

```
observability/langsmith/google-adk/code-debug-agent-demo/
├── README.md                          # This file
├── pyproject.toml                     # Dependencies (includes langsmith)
├── .env.example                       # Environment variable template
├── src/
│   ├── agents.py                      # Agent definitions with traced callbacks
│   ├── tools.py                       # Tools with @traceable decorators
│   ├── traced_runner.py               # Advanced tracing wrapper (optional)
│   ├── runner.py                      # Standard runner with --traced flag
│   ├── prompts.py                     # System prompts
│   ├── services/
│   │   └── stackexchange_service.py   # Context provider (RAG)
│   └── scenarios/                     # Test scenarios (12+ files)
└── tests/
    ├── conftest.py
    └── test_agents.py                 # Functionality tests
```

## Troubleshooting

### LangSmith Not Capturing Traces

Ensure environment variables are set correctly:
```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=ls_...
export LANGSMITH_PROJECT=code-debug-agent
```

Also ensure you're using the `--traced` flag when running scenarios.

### Google Gemini API Errors

**Rate Limit Errors (429 RESOURCE_EXHAUSTED):**

The free tier of Google Gemini API has a limit of **10 requests per minute** per model. When running all scenarios, you may hit this limit and see errors like:
```
429 RESOURCE_EXHAUSTED: You exceeded your current quota
```

**Solutions:**
1. **Use a stable model** instead of experimental: Set `GOOGLE_MODEL=gemini-2.0-flash` (default) instead of `gemini-2.0-flash-exp`
2. Run fewer scenarios at once (e.g., run specific scenario files instead of `--all-scenarios`)
3. Add delays between scenario runs
4. Use a paid Google Cloud project with higher quotas

**Available Models:**
- `gemini-2.0-flash` (default, stable with better rate limits)
- `gemini-1.5-flash` (previous generation, stable)
- `gemini-1.5-pro` (more capable but slower)
- `gemini-2.0-flash-exp` (experimental, lower rate limits)

**API Key Configuration:**

Verify your API key is valid:
```bash
export GOOGLE_API_KEY=your-api-key
export GOOGLE_GENAI_USE_VERTEXAI=0
```

This implementation uses the **direct Google Gemini API**, not Vertex AI. Get your API key from: https://aistudio.google.com/app/apikey

### Stack Exchange Rate Limiting

Without an API key, you're limited to 300 requests/day. For higher limits:
1. Register at https://stackapps.com/apps/oauth/register
2. Set `STACKEXCHANGE_API_KEY` environment variable

### Tests Pass But Tracing Doesn't Work

If tests pass but you don't see traces in LangSmith:
1. Verify `LANGSMITH_API_KEY` is set correctly
2. Check you're using the `--traced` flag
3. Ensure `LANGSMITH_TRACING=true` is set
4. Check LangSmith dashboard for correct project name

## Comparison with Langfuse Implementation

This implementation follows similar patterns to the Langfuse version at `observability/langfuse/google-adk/code-debug-agent-demo/` but uses LangSmith's SDK:

| Aspect | Langfuse | LangSmith |
|--------|----------|-----------|
| **Decorator** | `@observe` | `@traceable` |
| **Run Types** | Custom types | Standard (tool, chain, llm) |
| **Client Init** | `get_client()` | `Client()` |
| **Trace Context** | `update_current_trace()` | Automatic via decorator |

## Resources

- [Google ADK Documentation](https://github.com/google/adk-python)
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Python SDK](https://github.com/langchain-ai/langsmith-sdk)
- [Stack Exchange API Docs](https://api.stackexchange.com/docs)

## License

This is a demonstration project for Google ADK with LangSmith observability integration.
