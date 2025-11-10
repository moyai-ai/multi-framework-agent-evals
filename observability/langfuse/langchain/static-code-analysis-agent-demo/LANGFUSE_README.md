# Static Code Analysis Agent with Langfuse Observability

This is an instrumented version of the LangGraph ReAct agent for static code analysis, enhanced with **Langfuse** for full observability and tracing.

## Overview

This agent demonstrates how to integrate Langfuse tracing into a LangGraph-based agentic application, providing comprehensive observability for:

- **LLM Calls**: Track all model invocations with inputs, outputs, tokens, and costs
- **Tool Executions**: Monitor GitHub MCP tools, OpenGrep analysis, and dependency checks
- **Agent Workflow**: Visualize the ReAct loop (Reasoning → Action → Observation)
- **Node-level Tracing**: Detailed spans for each graph node execution
- **End-to-end Traces**: Complete analysis sessions grouped under unified traces

## Architecture

The agent uses LangGraph's ReAct pattern with Langfuse instrumentation:

```
┌─────────────────────────────────────────┐
│     Langfuse Top-Level Trace            │
│  (static-code-analysis)                 │
└──────────────┬──────────────────────────┘
               │
        ┌──────▼────────┐
        │  Reasoning    │ ← Span with input/output
        │  Node         │
        └──────┬────────┘
               │
        ┌──────▼────────┐
        │  Action       │ ← Tool calls traced
        │  Node         │   (fetch, analyze, etc.)
        └──────┬────────┘
               │
        ┌──────▼────────┐
        │  Observation  │ ← Results processing
        │  Node         │
        └──────┬────────┘
               │
        ┌──────▼────────┐
        │  Report       │ ← Final report generation
        │  Node         │
        └───────────────┘
```

## Key Features

### 1. Comprehensive Tracing

- **Top-level trace**: Groups entire analysis session
- **Node spans**: Individual spans for reasoning, action, observation, and report nodes
- **LLM tracing**: Automatic capture of all OpenAI API calls
- **Tool tracing**: Visibility into GitHub MCP and OpenGrep operations
- **Metadata**: Repository URL, analysis type, model configuration

### 2. Observable Context

Each trace captures:
- Repository being analyzed
- Analysis type (security, quality, dependencies)
- Number of files analyzed
- Issues found
- Steps taken
- Model configuration (name, temperature)
- Status (completed, error)

### 3. Node-Level Observability

**Reasoning Node**:
- Input: Current step, files to analyze, files analyzed, issues found
- Output: Tool calls decision, continuation status

**Action Node**:
- Traces tool executions (GitHub API calls, OpenGrep scans)
- Captures tool inputs and outputs

**Observation Node**:
- Processes tool results
- Tracks progress metrics

**Report Node**:
- Final report generation
- Summary of findings

## Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key
- Langfuse account (free at [cloud.langfuse.com](https://cloud.langfuse.com))

### Installation

1. Install dependencies:
```bash
cd observability/langfuse/langchain/static-code-analysis-agent-demo
unset VIRTUAL_ENV && uv sync
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
```bash
# OpenAI
OPENAI_API_KEY=your-openai-key

# Langfuse (get from https://cloud.langfuse.com)
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_ENABLED=true
```

### Getting Langfuse Credentials

1. Sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. Create a new project
3. Go to **Settings** → **API Keys**
4. Copy your **Public Key** and **Secret Key**
5. Add them to your `.env` file

## Usage

### Basic Usage

Run a static code analysis with full Langfuse tracing:

```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.manager "https://github.com/example/repo"
```

### Analysis Types

```bash
# Security analysis
uv run --env-file .env python -m src.manager "https://github.com/example/repo" --type security

# Code quality analysis
uv run --env-file .env python -m src.manager "https://github.com/example/repo" --type quality

# Dependency analysis
uv run --env-file .env python -m src.manager "https://github.com/example/repo" --type dependencies
```

### Python API

```python
import asyncio
from src.manager import AnalysisManager
from src.context import Config

async def main():
    # Configure with Langfuse enabled
    config = Config()
    config.LANGFUSE_ENABLED = True

    # Create manager
    manager = AnalysisManager(config=config, verbose=True)

    # Run analysis with tracing
    result = await manager.analyze_repository(
        repository_url="https://github.com/example/repo",
        analysis_type="security"
    )

    print(f"Trace captured in Langfuse!")
    print(f"Files analyzed: {len(result['files_analyzed'])}")
    print(f"Issues found: {len(result['issues_found'])}")

asyncio.run(main())
```

## Viewing Traces in Langfuse

After running an analysis:

1. Go to [cloud.langfuse.com](https://cloud.langfuse.com)
2. Navigate to **Traces** in your project
3. Find the trace tagged with `static-analysis` and your analysis type
4. Explore the trace tree to see:
   - LLM calls with prompts and responses
   - Tool executions with inputs/outputs
   - Node-level spans with timing
   - Metadata and tags
   - Token usage and costs

### Trace Structure

Each trace includes:

```
Trace: static-code-analysis
├── Tags: ["static-analysis", "security", "langgraph"]
├── Input: {repository_url, analysis_type}
├── Output: {files_analyzed, issues_found, steps_taken, status}
├── Metadata: {model, temperature}
└── Spans:
    ├── reasoning-node (multiple iterations)
    │   ├── Input: {current_step, files_to_analyze, ...}
    │   ├── LLM Call (via CallbackHandler)
    │   └── Output: {has_tool_calls, should_continue, ...}
    ├── action-node
    │   └── Tool Executions (traced automatically)
    ├── observation-node
    │   └── Results processing
    └── report-node
        └── Final report generation
```

## Observability Features

### 1. Tool Tracing

All tool executions are automatically traced:
- `fetch_repository_info`: GitHub API calls
- `list_repository_files`: File discovery
- `get_file_content`: File retrieval
- `run_opengrep_analysis`: Static analysis scans
- `analyze_dependencies`: Dependency checks
- `summarize_findings`: Results aggregation

### 2. Context Propagation

Langfuse automatically groups all operations under the top-level trace, ensuring:
- Related operations are linked
- Parent-child relationships are maintained
- Sub-agent calls (if any) are nested correctly

### 3. Metadata and Tags

Each trace includes:
- **Tags**: `static-analysis`, analysis type (e.g., `security`), `langgraph`
- **Metadata**: Model name, temperature, configuration
- **Session ID**: Thread ID for conversation tracking

### 4. Performance Monitoring

Track:
- Total analysis duration
- Time per graph node
- LLM latency
- Tool execution time
- Token usage and costs

## Comparison with Untraced Agent

| Feature | Untraced Agent | Langfuse-Traced Agent |
|---------|---------------|----------------------|
| Location | `frameworks/langchain/static-code-analysis-agent-demo` | `observability/langfuse/langchain/static-code-analysis-agent-demo` |
| Dependencies | LangChain, LangGraph | + Langfuse |
| LLM Visibility | Print statements | Full traces in UI |
| Tool Visibility | Print statements | Detailed tool traces |
| Cost Tracking | None | Automatic token/cost tracking |
| Error Debugging | Console logs | Trace replay in UI |
| Performance Analysis | Manual timing | Built-in latency metrics |
| Production Ready | Limited | Full observability |

## Advanced Configuration

### Disable Tracing

```bash
# Temporarily disable for testing
LANGFUSE_ENABLED=false uv run python -m src.manager "https://github.com/example/repo"
```

### Custom Trace Names

Modify `graph.py` to customize trace names:

```python
trace_context = langfuse_client.start_as_current_span(
    name="my-custom-analysis",
    as_type="trace"
)
```

### Self-Hosted Langfuse

```bash
# Point to your self-hosted instance
LANGFUSE_HOST=https://langfuse.your-domain.com
```

## Testing

Run tests with Langfuse tracing:

```bash
# Unit tests
unset VIRTUAL_ENV && uv run pytest -m unit -v

# All tests
unset VIRTUAL_ENV && uv run pytest -v
```

Note: Tests use mock OpenGrep by default and won't send traces unless explicitly configured.

## Troubleshooting

### Traces Not Appearing

1. Check credentials:
```python
from langfuse import get_client
client = get_client()
print(client.auth_check())  # Should return True
```

2. Verify environment variables:
```bash
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY
```

3. Check Langfuse status:
```bash
# Look for "✓ Langfuse tracing enabled" in output
```

### Authentication Errors

- Ensure keys are correct (public key starts with `pk-lf-`, secret with `sk-lf-`)
- Check Langfuse host URL (default: `https://cloud.langfuse.com`)
- Verify network connectivity to Langfuse

### Missing Traces for Tools

Tool calls are traced automatically via the `CallbackHandler`. Ensure:
- Handler is passed to `agent.ainvoke()` config
- Tools are executed through LangChain's tool system
- No exceptions during tool execution

## Learning Resources

### Langfuse Documentation

- [LangChain Integration](https://langfuse.com/docs/integrations/langchain)
- [LangGraph Tracing](https://langfuse.com/docs/integrations/langgraph)
- [Python SDK](https://langfuse.com/docs/sdk/python)

### Key Concepts

1. **CallbackHandler**: Automatically traces LangChain/LangGraph operations
2. **start_as_current_span**: Creates custom spans for node-level tracing
3. **Trace Context**: Groups related operations under a single trace
4. **Tags & Metadata**: Organize and filter traces

## Next Steps

1. **Experiment**: Run analyses on different repositories
2. **Explore**: Navigate traces in Langfuse UI
3. **Optimize**: Use performance data to improve agent efficiency
4. **Monitor**: Set up alerts for errors or slow executions
5. **Evaluate**: Use Langfuse's evaluation features to assess agent quality

## Contributing

To add more observability:

1. Add spans for custom operations:
```python
with langfuse_client.start_as_current_span(name="custom-op") as span:
    span.update(input={"data": "..."})
    # Your operation
    span.update(output={"result": "..."})
```

2. Tag important operations:
```python
trace_context.update(tags=["new-tag"])
```

3. Add metadata:
```python
span.update(metadata={"custom_field": "value"})
```

## License

This is a demonstration project for educational purposes.

## Acknowledgments

- **Langfuse**: For the excellent observability platform
- **LangGraph**: For the graph-based agent framework
- **LangChain**: For the LLM integration tools
