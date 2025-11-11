# Static Code Analysis Agent Demo - LangSmith Observability

A LangGraph ReAct agent for static code analysis with comprehensive **LangSmith observability** integration.

## Overview

This demo showcases a LangGraph-based AI agent that performs static code analysis on GitHub repositories using:
- **LangChain & LangGraph**: For agent orchestration and ReAct pattern implementation
- **LangSmith**: For comprehensive observability, tracing, and monitoring
- **GitHub MCP**: For repository access
- **OpenGrep**: For security and code quality analysis

## Key Features

### Agent Capabilities
- 🔍 Security vulnerability detection
- 📊 Code quality analysis
- 📦 Dependency analysis
- 🔄 ReAct-style reasoning loop
- 📁 GitHub repository integration

### LangSmith Observability

This implementation leverages **LangSmith's automatic tracing** capabilities with the following features:

#### 1. **Automatic Tracing**
- Environment variable-based configuration (`LANGSMITH_TRACING=true`)
- Automatic capture of all LLM calls, tool executions, and agent steps
- No manual trace management required

#### 2. **Enhanced Metadata**
- Custom tags for filtering: `static-analysis`, `security`, `quality`, `production`
- Scenario tracking for evaluation
- Repository and analysis metadata
- Status tags: `success`, `error`, `has-critical-issues`, `has-high-issues`

#### 3. **Traceable Nodes**
Each graph node is decorated with `@traceable` for granular observability:
- `reasoning-node`: Tracks LLM reasoning and decision-making
- `action-node`: Monitors tool execution
- `observation-node`: Captures result processing
- `report-node`: Logs final report generation

#### 4. **Structured Logging**
- Severity breakdowns
- File analysis progress
- Issue categorization
- Performance metrics

## Installation

```bash
# Install dependencies
cd observability/langsmith/langchain/static-code-analysis-agent-demo
unset VIRTUAL_ENV && uv sync

# Or with pip
pip install -e .
```

## Configuration

Create a `.env` file with the following variables:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# LangSmith Configuration
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=static-code-analysis-agent
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# Optional
MODEL_NAME=gpt-4-turbo-preview
TEMPERATURE=0.3
GITHUB_TOKEN=your-github-token  # Optional, MCP may provide access
DEBUG=false
```

### LangSmith Setup

1. **Create a LangSmith Account**
   - Visit [smith.langchain.com](https://smith.langchain.com)
   - Sign up for a free account

2. **Get Your API Key**
   - Go to Settings → API Keys
   - Create a new API key
   - Copy it to your `.env` file

3. **Create a Project**
   - Go to Projects
   - Create a project named "static-code-analysis-agent" (or customize in `.env`)

4. **View Traces**
   - Run your agent
   - Go to your project in LangSmith
   - View detailed traces, metrics, and performance data

## Usage

### Basic Usage

```python
from src.agent.graph import run_agent_sync

# Run analysis
result = run_agent_sync(
    repository_url="https://github.com/owner/repo",
    analysis_type="security"
)

print(f"Files analyzed: {len(result['files_analyzed'])}")
print(f"Issues found: {len(result['issues_found'])}")
print(result['final_report'])
```

### With User and Session Tracking

```python
from src.agent.graph import run_agent
import asyncio

async def main():
    result = await run_agent(
        repository_url="https://github.com/owner/repo",
        analysis_type="security",
        user_id="analyst-001",
        session_id="session-12345",
        scenario_name="vulnerability-scan"
    )
    return result

result = asyncio.run(main())
```

### Running Scenarios with LangSmith Tracing

```bash
# Run all scenarios (automatically traced)
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner --all-scenarios

# Run a single scenario
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/security_vulnerabilities.json

# View traces in LangSmith dashboard
```

## LangSmith Observability Features

### Trace Enrichment

Every trace includes:

```python
{
    "tags": [
        "static-analysis",
        "security",
        "langgraph",
        "production",
        "scenario:vulnerability-scan",
        "success",  # or "error"
        "has-critical-issues"  # conditional
    ],
    "metadata": {
        "agent": "static-code-analysis-agent",
        "version": "1.0.0",
        "repository_url": "...",
        "analysis_type": "security",
        "model": "gpt-4-turbo-preview",
        "temperature": 0.3,
        "user_id": "analyst-001",
        "session_id": "session-12345",
        "scenario": "vulnerability-scan"
    }
}
```

### Node-Level Tracing

Each node in the graph provides detailed insights:

**Reasoning Node:**
- Input: Current state (files, issues, step count)
- Output: LLM decision, tool calls, continuation status
- Metrics: Response time, token usage

**Action Node:**
- Input: Tool calls from LLM
- Output: Tool execution results
- Metrics: Tool execution time, success/failure

**Observation Node:**
- Input: Tool results
- Output: Updated state with parsed results
- Metrics: Issues found, files processed

**Report Node:**
- Input: All findings and analysis summary
- Output: Final formatted report
- Metrics: Report generation time

### Filtering and Analysis in LangSmith

In the LangSmith dashboard, you can filter traces by:
- **Analysis type**: `security`, `quality`, `dependencies`
- **Status**: `success`, `error`
- **Issue severity**: `has-critical-issues`, `has-high-issues`
- **Scenario name**: e.g., `scenario:vulnerability-scan`
- **User ID**: Track usage by analyst
- **Time range**: Daily, weekly, monthly views

## Architecture

### Agent Flow

```
Start
  ↓
Reasoning Node → LLM decides next action
  ↓
Has Tool Calls?
  ├─ Yes → Action Node → Execute tools
  │         ↓
  │    Observation Node → Process results
  │         ↓
  │    Check if complete?
  │         ├─ No → Back to Reasoning
  │         └─ Yes ↓
  └─ No → Report Node → Generate final report
           ↓
          End
```

### Tools Available

1. **fetch_repository_info** - Get repository metadata
2. **list_repository_files** - List files in repository
3. **get_file_content** - Retrieve file contents
4. **run_opengrep_analysis** - Run security/quality scans
5. **analyze_dependencies** - Check for dependency issues
6. **summarize_findings** - Generate issue summaries

## Testing

```bash
# Run all tests (automatically uses mock OpenGrep)
unset VIRTUAL_ENV && uv run pytest

# Run with coverage
unset VIRTUAL_ENV && uv run pytest --cov=src

# Run specific test categories
unset VIRTUAL_ENV && uv run pytest -m unit
unset VIRTUAL_ENV && uv run pytest -m scenario
```

## Observability Best Practices

### 1. Use Descriptive Scenario Names
```python
scenario_name = f"{analysis_type}_scan_{repo_name}"
```

### 2. Track User Sessions
```python
from datetime import datetime
session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
```

### 3. Monitor Critical Metrics
- Trace count and success rate
- Average execution time
- Issue detection rate
- False positive rate

### 4. Set Up Alerts in LangSmith
Configure alerts for:
- Trace failures
- Long execution times (> 2 minutes)
- High token usage
- Critical issues detected

## Comparison: LangSmith vs. Langfuse

| Feature | LangSmith | Langfuse |
|---------|-----------|----------|
| **Setup** | Environment variables | Callback handler initialization |
| **Tracing** | Automatic via env vars | Manual callback passing |
| **Decorators** | `@traceable` | Manual span management |
| **Metadata** | Config-based | Programmatic updates |
| **Integration** | Native LangChain | Third-party callback |
| **Overhead** | Minimal | Moderate |

### Key Differences

**LangSmith Advantages:**
- ✅ Simpler setup (just environment variables)
- ✅ Native LangChain integration
- ✅ Automatic trace capture
- ✅ `@traceable` decorator for any function
- ✅ Zero code changes to enable/disable tracing

**Langfuse Advantages:**
- ✅ More granular control over spans
- ✅ Explicit trace lifecycle management
- ✅ Custom span attributes via context managers

### Implementation Comparison

**LangSmith:**
```python
# Just set environment variables
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "..."

# Use @traceable decorator
@traceable(name="my-node", run_type="chain")
async def my_node(state):
    return state
```

**Langfuse:**
```python
# Initialize handler
from langfuse.langchain import CallbackHandler
handler = CallbackHandler()

# Pass to LLM calls
response = await llm.ainvoke(messages, config={"callbacks": [handler]})

# Manual span management
with langfuse_client.start_as_current_span(name="my-node") as span:
    # work
    span.update(output={"result": "..."})
```

## Project Structure

```
observability/langsmith/langchain/static-code-analysis-agent-demo/
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py          # Main agent with @traceable decorators
│   │   ├── state.py          # Agent state management
│   │   └── prompts.py        # System and reasoning prompts
│   ├── tools/
│   │   ├── github_tools.py   # Repository access tools
│   │   ├── opengrep_tools.py # Static analysis tools
│   │   └── analysis_tools.py # Result processing tools
│   ├── context.py            # Configuration with LangSmith settings
│   ├── manager.py            # Analysis orchestration
│   └── runner.py             # Scenario execution
├── tests/
│   ├── test_agent.py
│   ├── test_scenarios.py
│   └── conftest.py
├── pyproject.toml
├── README.md                  # General documentation
└── LANGSMITH_README.md       # This file (LangSmith-specific)
```

## Troubleshooting

### Traces Not Appearing in LangSmith

1. **Verify environment variables:**
   ```bash
   echo $LANGSMITH_TRACING
   echo $LANGSMITH_API_KEY
   echo $LANGSMITH_PROJECT
   ```

2. **Check API key validity:**
   - Go to LangSmith dashboard
   - Settings → API Keys
   - Verify your key is active

3. **Ensure project exists:**
   - Go to Projects
   - Create project if it doesn't exist
   - Or set `LANGSMITH_PROJECT` to existing project name

4. **Network connectivity:**
   ```bash
   curl -I https://api.smith.langchain.com
   ```

### LangSmith vs Local Development

For local development without LangSmith:
```bash
LANGSMITH_TRACING=false
```

The agent will still run but without observability tracing.

### Debugging Tracing Issues

Enable debug mode:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

Check the console output for:
```
✓ LangSmith tracing enabled - Project: static-code-analysis-agent
```

## Advanced Features

### Custom Trace Names

The `run_agent` function automatically generates descriptive trace names:
```python
# Trace name format:
"static-code-analysis-agent: {analysis_type} analysis [{scenario_name}] - {repo_name}"
```

Example:
```
"static-code-analysis-agent: security analysis [vulnerability-scan] - owner/repo"
```

### Session Tracking

Group related analyses by session:
```python
result = await run_agent(
    repository_url="...",
    session_id="daily-scan-2025-01-11"
)
```

Filter by session in LangSmith to see all analyses in that session.

### User Attribution

Track which analyst performed the analysis:
```python
result = await run_agent(
    repository_url="...",
    user_id="analyst-sarah"
)
```

Analyze performance metrics per user in LangSmith.

## Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangChain Observability Guide](https://python.langchain.com/docs/langsmith/observability)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Original Framework Demo](../../../../frameworks/langchain/static-code-analysis-agent-demo/)
- [Langfuse Implementation](../../langfuse/langchain/static-code-analysis-agent-demo/)

## License

MIT

## Contributing

Contributions welcome! Please ensure LangSmith tracing is properly configured in tests and examples.

When contributing:
1. Maintain `@traceable` decorators on all node functions
2. Include meaningful metadata and tags
3. Test with `LANGSMITH_TRACING=false` to ensure it works without observability
4. Document any new observability features
