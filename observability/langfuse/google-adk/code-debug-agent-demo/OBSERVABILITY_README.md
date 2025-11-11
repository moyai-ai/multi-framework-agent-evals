# Code Debug Agent - Langfuse Observability Implementation

This is a fully instrumented version of the Google ADK Code Debug Agent with comprehensive Langfuse tracing for production observability.

## What's Different from the Original?

This traced version provides **full observability** into the agent's execution:

### 1. **Agent-Level Tracing** (`@observe(as_type="agent")`)
- Main agent execution flows are traced as agent operations
- Tracks overall execution time, inputs, and outputs
- Captures session and user context

### 2. **Tool Call Tracing** (`@observe(as_type="tool")`)
All four debug tools are instrumented:
- `search_stack_exchange_for_error` - Traced with input/output
- `search_stack_exchange_general` - Full parameter tracking
- `get_stack_exchange_answers` - Answer retrieval monitoring
- `analyze_error_and_suggest_fix` - Analysis workflow visibility

### 3. **RAG/Retrieval Tracing** (`@observe(as_type="retriever")`)
Stack Exchange service methods tracked as retrievers:
- `search_questions` - Query and result metrics
- `get_answers` - Answer fetching operations
- `search_similar_errors` - Error similarity search

### 4. **Sub-Agent Tracing** (for Sequential Agents)
- Error analyzer sub-agent traced separately
- Solution finder sub-agent traced separately
- Full visibility into multi-step workflows

### 5. **Enhanced Callbacks with Langfuse**
- `_format_debug_response` callback enhanced with trace updates
- Response metadata captured (length, content preview)
- Error states logged to Langfuse

## Files Modified for Tracing

### Core Implementation Files
1. **`src/agents.py`**
   - Added Langfuse imports
   - Enhanced callbacks with trace updates
   - Error logging to Langfuse

2. **`src/tools.py`**
   - All tool functions decorated with `@observe(as_type="tool")`
   - Input/output automatically captured
   - Tool execution timing tracked

3. **`src/services/stackexchange_service.py`**
   - Service methods decorated with `@observe(as_type="retriever")`
   - RAG operations fully traced
   - API call metrics captured

### New Files
4. **`src/traced_runner.py`** (NEW)
   - `TracedAgentRunner` class for comprehensive agent tracing
   - `run_traced_scenario` for scenario-based testing with observability
   - `run_debug_agent_traced` convenience function
   - Full session and user context management

5. **`.env.example`** (NEW)
   - Configuration template for Langfuse credentials
   - Google API and optional Stack Exchange API keys

6. **`OBSERVABILITY_README.md`** (this file)
   - Documentation for the tracing implementation

### Configuration Files
7. **`pyproject.toml`**
   - Added `langfuse>=2.0.0` dependency
   - Updated project name to `code-debug-agent-demo-traced`

## Installation

```bash
# Navigate to the traced agent directory
cd observability/langfuse/google-adk/code-debug-agent-demo

# Install dependencies (requires uv)
unset VIRTUAL_ENV && uv sync

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Required Environment Variables

```bash
# Required for agent execution
GOOGLE_API_KEY=your_google_api_key_here

# Required for Langfuse observability
LANGFUSE_PUBLIC_KEY=pk-lf-your_public_key_here
LANGFUSE_SECRET_KEY=sk-lf-your_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com  # or your self-hosted instance
```

## Usage Examples

### Example 1: Simple Query with Tracing

```python
import asyncio
from src.traced_runner import run_debug_agent_traced

async def main():
    response = await run_debug_agent_traced(
        prompt="ImportError: No module named 'pandas'",
        agent_name="debug_agent",
        user_id="user_123",
        session_id="session_456"
    )
    print(f"Response: {response}")

asyncio.run(main())
```

### Example 2: Using TracedAgentRunner Directly

```python
import asyncio
from src.traced_runner import TracedAgentRunner

async def main():
    # Initialize the traced runner
    runner = TracedAgentRunner(
        agent_name="quick_debug_agent",
        app_name="debug-assistant"
    )

    # Run with streaming events
    async for event in runner.run_traced(
        prompt="TypeError: Cannot read property 'map' of undefined",
        user_id="test_user",
        session_id="test_session",
        metadata={"source": "web_app", "priority": "high"}
    ):
        print(f"Event: {event}")

asyncio.run(main())
```

### Example 3: Scenario Testing with Observability

```python
import asyncio
from src.traced_runner import run_traced_scenario

async def main():
    scenario = {
        "name": "Python Import Error Test",
        "description": "Test handling of missing module errors",
        "error_message": "ModuleNotFoundError: No module named 'numpy'",
        "programming_language": "python",
        "expected_tools": ["search_stack_exchange_for_error"]
    }

    result = await run_traced_scenario(
        scenario_data=scenario,
        agent_name="debug_agent",
        user_id="tester_001"
    )

    print(f"Success: {result['success']}")
    print(f"Response: {result['response']}")

asyncio.run(main())
```

### Example 4: Running Scenarios from JSON

```bash
# Create a script that uses the traced runner
# run_traced_example.py

import asyncio
import json
from pathlib import Path
from src.traced_runner import run_traced_scenario

async def main():
    # Load scenario
    scenario_file = Path("src/scenarios/python_import_error_missing_module.json")
    with open(scenario_file) as f:
        data = json.load(f)

    # Run each scenario with tracing
    for scenario in data.get("scenarios", []):
        print(f"\n{'='*60}")
        print(f"Running scenario: {scenario['name']}")
        print(f"{'='*60}")

        result = await run_traced_scenario(
            scenario_data=scenario,
            agent_name="debug_agent",
            user_id="scenario_tester"
        )

        print(f"Result: {result}")

asyncio.run(main())
```

Then run it:
```bash
unset VIRTUAL_ENV && uv run python run_traced_example.py
```

## What Gets Traced?

### Trace Hierarchy

```
Trace: "Agent Execution: debug_agent"
├── Span: debug_agent_execution (agent)
│   ├── Input: {prompt, agent_name}
│   ├── Output: {total_events, response_summary}
│   ├── Metadata: {agent_model, events_processed}
│   │
│   ├── Span: search_stack_exchange_for_error (tool)
│   │   ├── Input: {error_message, programming_language, framework, ...}
│   │   ├── Output: {success, results, total_results}
│   │   ├── Metadata: {execution_time}
│   │   │
│   │   └── Span: search_similar_errors (retriever)
│   │       ├── Input: {error_message, limit}
│   │       ├── Output: {success, results}
│   │       └── Metadata: {search_keywords, quota_remaining}
│   │
│   └── Span: _format_debug_response (callback)
│       ├── Input: {response}
│       ├── Output: {response_preview, response_length}
│       └── Metadata: {formatting_applied}
```

### Captured Metrics

1. **Execution Metrics**
   - Total execution time per agent call
   - Tool invocation count and duration
   - RAG retrieval latency
   - Event processing count

2. **Context Information**
   - User ID and session ID
   - Prompt length and content
   - Agent name and model
   - Response length and preview

3. **Error Tracking**
   - Exception types and messages
   - Stack traces (via Langfuse error capture)
   - Failed tool calls
   - API errors from Stack Exchange

4. **RAG/Retrieval Metrics**
   - Search queries and keywords
   - Results returned per query
   - Stack Exchange quota usage
   - Answer relevance scores

## Viewing Traces in Langfuse

1. **Navigate to your Langfuse dashboard** at https://cloud.langfuse.com (or your self-hosted URL)

2. **View Traces**: Go to the "Traces" tab to see all agent executions

3. **Filter by Tags**: Use tags like `google-adk`, `debug-agent` to filter

4. **Analyze Performance**:
   - Sort by execution time to find slow queries
   - Check tool call frequency
   - Monitor error rates

5. **Session Analysis**: Group traces by session_id to see conversation flows

6. **User Analysis**: Filter by user_id to track individual user experiences

## Comparison: Traced vs Untraced Agent

### Original Agent (frameworks/google-adk/code-debug-agent-demo)
- ✅ Functional debugging agent
- ❌ No visibility into tool calls
- ❌ No RAG operation tracking
- ❌ Limited error diagnostics
- ❌ No performance metrics

### Traced Agent (observability/langfuse/google-adk/code-debug-agent-demo)
- ✅ Full execution visibility
- ✅ Tool call tracking with inputs/outputs
- ✅ RAG operation monitoring
- ✅ Comprehensive error logging
- ✅ Performance metrics and analytics
- ✅ User and session tracking
- ✅ Production-ready observability

## Advanced Configuration

### Custom Trace Metadata

```python
from src.traced_runner import TracedAgentRunner

runner = TracedAgentRunner(agent_name="debug_agent")

await runner.run_traced(
    prompt="Your error here",
    metadata={
        "environment": "production",
        "region": "us-west-2",
        "customer_tier": "premium",
        "feature_flags": {"new_ui": True}
    }
)
```

### Disable Tracing (for testing)

```bash
# In .env
LANGFUSE_TRACING_ENABLED=false
```

### Debug Mode

```bash
# In .env
LANGFUSE_DEBUG=true
DEBUG=true
```

## Testing with Observability

```bash
# Run all tests with tracing enabled
unset VIRTUAL_ENV && uv run pytest -v

# Run specific traced scenario
unset VIRTUAL_ENV && uv run python -m src.runner \
    src/scenarios/python_import_error_missing_module.json \
    debug_agent
```

## Performance Considerations

- **Overhead**: Langfuse adds ~5-10ms per traced operation (negligible for LLM calls)
- **Async Operations**: All tracing is non-blocking
- **Batching**: Langfuse batches trace data to minimize network calls
- **Sampling**: Can configure sampling rate if needed for high-volume scenarios

## Troubleshooting

### Traces Not Appearing?

1. Check Langfuse credentials in `.env`
2. Enable debug mode: `LANGFUSE_DEBUG=true`
3. Verify network connectivity to Langfuse host
4. Check that `LANGFUSE_TRACING_ENABLED=true`

### Agent Still Works Without Langfuse?

Yes! The tracing is designed to fail gracefully. If Langfuse is not configured, the agent continues to work normally without tracing.

### How to Compare Performance?

Run the same scenario on both versions:

```bash
# Original (untraced)
cd frameworks/google-adk/code-debug-agent-demo
unset VIRTUAL_ENV && uv run python -m src.runner src/scenarios/python_import_error.json

# Traced version
cd observability/langfuse/google-adk/code-debug-agent-demo
unset VIRTUAL_ENV && uv run python -m src.runner src/scenarios/python_import_error.json
```

Compare execution times in terminal vs. detailed metrics in Langfuse dashboard.

## Learning Resources

### Understanding the Implementation

1. **Start with**: `src/traced_runner.py` - Main tracing orchestration
2. **Then review**: `src/tools.py` - Tool-level tracing
3. **Finally check**: `src/services/stackexchange_service.py` - RAG tracing

### Langfuse Documentation

- [Langfuse Python SDK](https://langfuse.com/docs/sdk/python)
- [@observe Decorator](https://langfuse.com/docs/sdk/python/decorators)
- [Trace Types](https://langfuse.com/docs/tracing)

### Google ADK Documentation

- [Google ADK Docs](https://google.github.io/adk-docs/)
- [ADK Python GitHub](https://github.com/google/adk-python)

## Contributing

When adding new features:

1. Add `@observe` decorators to new tools (use `as_type="tool"`)
2. Add `@observe` decorators to RAG operations (use `as_type="retriever"`)
3. Use `langfuse.update_current_span()` for detailed metadata
4. Test that tracing works with and without Langfuse configured

## License

Same as the original Code Debug Agent Demo - see parent README.md

## Questions?

For questions about:
- **Langfuse integration**: See [Langfuse Documentation](https://langfuse.com/docs)
- **Google ADK**: See [ADK Documentation](https://google.github.io/adk-docs/)
- **This implementation**: Review the code comments in `src/traced_runner.py`
