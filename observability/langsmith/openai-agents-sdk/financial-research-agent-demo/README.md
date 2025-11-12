# Financial Research Multi-Agent System with LangSmith Observability

A sophisticated multi-agent system for financial research, built with OpenAI Agents SDK and instrumented with LangSmith for comprehensive observability and tracing.

## Overview

This demo showcases a complete financial research workflow orchestrated by multiple specialized agents:

1. **Planner Agent** - Creates search strategy from user query
2. **Search Agent** - Executes web searches for information
3. **Financials Analyst Agent** - Analyzes company financial metrics
4. **Risk Analyst Agent** - Assesses business risks
5. **Writer Agent** - Synthesizes comprehensive research reports
6. **Verifier Agent** - Validates report quality and consistency

## LangSmith Observability

This implementation provides full observability through LangSmith:

### Instrumentation Layers

1. **Workflow-Level Tracing**
   - Overall research workflow traced with `@traceable` decorator
   - Captures end-to-end execution with metadata and tags

2. **Agent-Level Tracing**
   - Each agent execution (planning, searching, writing, verifying) traced as separate spans
   - Automatic tracking of inputs, outputs, and execution time

3. **Tool-Level Tracing**
   - All function tools (`web_search_tool`, `company_financials_tool`, `risk_analysis_tool`, `market_data_tool`) traced
   - Captures tool invocations with parameters and results

4. **LLM-Level Tracing**
   - LLM calls automatically traced by LangSmith
   - Token usage, latency, and model parameters captured

### Key Features

- **Hierarchical Trace Structure**: Nested spans showing the complete workflow
- **Metadata Enrichment**: Each span includes relevant context (agent name, step, query, etc.)
- **Error Tracking**: Automatic capture of exceptions and errors
- **Performance Metrics**: Execution time, token usage, and latency for each component
- **Search Correlation**: Group traces by user_id or session for multi-turn analysis

## Architecture

```
FinancialResearchManager (@traceable workflow)
├── plan_searches (@traceable chain)
│   └── Runner.run(planner_agent) [auto-traced]
│       └── LLM calls [auto-traced]
├── perform_searches (@traceable chain)
│   └── search_single_term x N (@traceable chain)
│       └── Runner.run(search_agent) [auto-traced]
│           ├── web_search_tool (@traceable tool)
│           └── LLM calls [auto-traced]
├── write_report (@traceable chain)
│   └── Runner.run(writer_agent) [auto-traced]
│       ├── company_financials_tool (@traceable tool)
│       ├── risk_analysis_tool (@traceable tool)
│       ├── market_data_tool (@traceable tool)
│       └── LLM calls [auto-traced]
└── verify_report (@traceable chain)
    └── Runner.run(verifier_agent) [auto-traced]
        └── LLM calls [auto-traced]
```

## Installation

1. **Clone the repository and navigate to this directory**

```bash
cd observability/langsmith/openai-agents-sdk/financial-research-agent-demo
```

2. **Install dependencies using uv**

```bash
uv sync
```

3. **Set up environment variables**

Create a `.env` file with:

```bash
OPENAI_API_KEY=sk-...
LANGSMITH_API_KEY=ls_...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=financial-research-agents  # Optional: specify project name
```

## Usage

### Interactive Mode

Run the manager directly for interactive queries:

```bash
uv run --env-file .env python -m src.manager
```

Or provide a query as command line arguments:

```bash
uv run --env-file .env python -m src.manager "Analyze Apple Inc's Q4 2024 performance"
```

### Scenario-Based Testing

Run predefined test scenarios:

```bash
# Run a specific scenario
uv run --env-file .env python -m src.runner src/scenarios/company_analysis.json --verbose

# Run all scenarios
uv run --env-file .env python -m src.runner --all-scenarios --verbose

# Save reports
uv run --env-file .env python -m src.runner --all-scenarios --output reports/
```

## Available Scenarios

- `company_analysis.json` - Analyze a specific company's financial performance
- `market_research.json` - Research a market segment or trend
- `competitor_analysis.json` - Compare multiple companies in a sector

## Viewing Traces in LangSmith

After running the agents, view your traces in LangSmith:

1. Visit [https://smith.langchain.com/](https://smith.langchain.com/)
2. Select your project (default: "financial-research-agents")
3. Browse traces to see:
   - Complete workflow execution
   - Individual agent performances
   - Tool invocations with parameters
   - LLM calls with prompts and responses
   - Token usage and costs
   - Error tracking and debugging info

### Analyzing Traces

Use LangSmith's features to:
- **Compare runs**: See performance differences across queries
- **Debug failures**: Identify where and why agents fail
- **Optimize costs**: Track token usage per agent/tool
- **Monitor latency**: Find bottlenecks in the workflow
- **Evaluate quality**: Use LangSmith's evaluation features

## Observability Comparison

### LangSmith vs Langfuse

Both implementations provide comprehensive observability, but with different approaches:

| Feature | LangSmith | Langfuse |
|---------|-----------|----------|
| Decorator | `@traceable` | `@observe` |
| SDK Integration | Native LangChain | Framework-agnostic |
| Trace Hierarchy | Automatic | Manual with `update_current_span` |
| UI/Dashboard | smith.langchain.com | cloud.langfuse.com |
| Evaluation Tools | Built-in | Built-in |
| Cost Tracking | Yes | Yes |

**Key Difference**: LangSmith uses `@traceable` decorator and provides automatic parent-child span relationships, while Langfuse uses `@observe` and requires explicit span updates via `get_client()`.

## Project Structure

```
financial-research-agents-demo/
├── src/
│   ├── __init__.py
│   ├── context.py          # Context models and helpers
│   ├── agents.py           # 6 agent definitions
│   ├── tools.py            # Tool implementations
│   ├── manager.py          # Orchestration manager
│   ├── runner.py           # Scenario test runner
│   └── scenarios/
│       ├── company_analysis.json
│       ├── market_research.json
│       └── competitor_analysis.json
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   └── test_agents.py      # Comprehensive test suite
├── pyproject.toml
├── README.md
└── .env
```

## Key Features

### Multi-Agent Orchestration

The system coordinates multiple specialized agents to perform complex research:

```python
from src.manager import FinancialResearchManager

manager = FinancialResearchManager(verbose=True)
result = await manager.run("Analyze Apple Inc's recent performance")
```

### Context Preservation

Financial research state is maintained throughout the workflow:

```python
context = FinancialResearchContext(
    query="Analyze Apple Inc",
    company_name="Apple Inc",
    search_plan=["Apple earnings", "Apple iPhone sales"],
    current_stage="searching"
)
```

### Concurrent Search Execution

Multiple searches execute in parallel for efficiency:

```python
# Searches run concurrently
search_results = await manager._perform_searches(search_terms)
```

### Analyst-as-Tool Pattern

Specialist agents are exposed as tools to the Writer agent:

```python
writer_agent = Agent(
    name="Writer Agent",
    tools=[company_financials_tool, risk_analysis_tool]
)
```

## Testing

Run unit tests:

```bash
uv run pytest
```

Run integration tests (requires API keys):

```bash
uv run pytest -m integration
```

## Troubleshooting

### Traces Not Appearing

1. Verify `LANGSMITH_API_KEY` is set correctly
2. Ensure `LANGSMITH_TRACING=true` is set
3. Check console output for any LangSmith connection errors
4. Verify you're looking at the correct project in LangSmith UI

### API Rate Limits

If you hit OpenAI rate limits:
- Reduce concurrent searches in `manager.py`
- Add delays between agent calls
- Use a different model (e.g., `gpt-4o-mini`)

### Missing Dependencies

Ensure all dependencies are installed:

```bash
uv sync --all-extras
```

## License

MIT

## Related Implementations

- **Non-traced version**: `frameworks/openai-agents-sdk/financial-research-agents-demo`
- **Langfuse version**: `observability/langfuse/openai-agents-sdk/financial-research-agent-demo`
- **Google ADK + LangSmith**: `observability/langsmith/google-adk/code-debug-agent-demo`
- **LangChain + LangSmith**: `observability/langsmith/langchain/static-code-analysis-agent-demo`
