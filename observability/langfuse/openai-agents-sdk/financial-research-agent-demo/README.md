# OpenAI Agents SDK - Financial Research Multi-Agent Demo

A comprehensive demonstration of the OpenAI Agents SDK featuring a multi-agent financial research system with orchestrated workflows and test-driven development.

## Overview

This project implements a complete financial research agent system using the OpenAI Agents SDK. It demonstrates:
- **Multi-agent orchestration** with specialized analyst agents
- **Concurrent execution** of search tasks
- **Tool integration** for financial analysis
- **Context management** across agent workflows
- **Test-driven approach** with JSON-based scenarios

## Architecture

### 6 Specialized Agents

1. **Planner Agent** - Transforms user queries into structured search strategies
2. **Search Agent** - Executes web searches for financial information
3. **Financials Analyst Agent** - Analyzes company financial metrics (used as tool by Writer)
4. **Risk Analyst Agent** - Assesses business risks (used as tool by Writer)
5. **Writer Agent** - Synthesizes comprehensive research reports
6. **Verifier Agent** - Validates report quality and consistency

### Workflow

```
User Query
    ↓
[Planner Agent] → Search Terms
    ↓
[Search Agent] → Search Results (concurrent)
    ↓
[Writer Agent] → Draft Report
    ↓         ↗ [Financials Analyst]
              ↗ [Risk Analyst]
    ↓
[Verifier Agent] → Final Report
```

### 4 Function Tools

- `web_search_tool` - Search for financial data and market information
- `company_financials_tool` - Analyze financial metrics and performance
- `risk_analysis_tool` - Assess business risks and mitigants
- `market_data_tool` - Retrieve current market data and prices

## Installation

1. Install dependencies with uv:
```bash
unset VIRTUAL_ENV && uv sync
```

## Usage

### Interactive Research

Run the manager interactively:
```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.manager
```

Or provide a query directly:
```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.manager "Analyze Apple Inc's Q4 2024 performance"
```

### Running Test Scenarios

Execute a single scenario:
```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/company_analysis.json --verbose
```

Run all scenarios:
```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner --all-scenarios --verbose
```

### Running Tests with Pytest

**Unit tests**:
```bash
# Run all unit tests
unset VIRTUAL_ENV && uv run pytest

# Run specific test classes
unset VIRTUAL_ENV && uv run pytest tests/test_agents.py::TestContext -v
unset VIRTUAL_ENV && uv run pytest tests/test_agents.py::TestAgents -v
unset VIRTUAL_ENV && uv run pytest tests/test_agents.py::TestTools -v
unset VIRTUAL_ENV && uv run pytest tests/test_agents.py::TestScenarioRunner -v
```

**Integration tests** (requires valid API key):
```bash
# Run integration tests
unset VIRTUAL_ENV && uv run --env-file .env pytest -m integration -v

# Run specific integration test
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/test_agents.py::TestIntegration::test_simple_research_flow -v

# Full scenario tests (requires API key and flag)
unset VIRTUAL_ENV && RUN_FULL_SCENARIOS=1 uv run --env-file .env pytest tests/test_agents.py::TestIntegration::test_full_scenarios -v
```

**All tests** (unit + integration):
```bash
unset VIRTUAL_ENV && uv run --env-file .env pytest -m tests/ -v
```

## Scenario JSON Format

Scenarios are defined in JSON with the following structure:

```json
{
  "name": "Scenario Name",
  "description": "What this scenario tests",
  "query": "The financial research query",
  "expectations": {
    "min_search_terms": 3,
    "required_sections": ["Executive Summary", "Financial Performance"],
    "verification_should_pass": true,
    "min_report_length": 500,
    "required_keywords": ["revenue", "growth"]
  },
  "metadata": {
    "test_type": "company_analysis",
    "priority": "high"
  }
}
```

## Available Test Scenarios

1. **company_analysis.json** - Comprehensive company financial analysis (Apple Inc)
2. **market_research.json** - Market sector research (AI Semiconductors)
3. **competitor_analysis.json** - Competitive landscape analysis (Tesla vs Rivian)

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

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `RUN_FULL_SCENARIOS` - Set to "1" to run full scenario tests in pytest
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Development

### Adding New Agents

1. Define the agent in `src/agents.py`:
```python
new_agent = Agent[FinancialResearchContext](
    name="New Agent",
    model="gpt-4o",
    instructions="Agent instructions...",
    tools=[tool1, tool2]
)
```

2. Add to AGENTS registry:
```python
AGENTS["new_agent"] = new_agent
```

### Adding New Tools

1. Create tool in `src/tools.py`:
```python
@function_tool(
    name_override="tool_name",
    description_override="Tool description"
)
async def tool_name(param1: str) -> str:
    # Tool logic
    return result
```

2. Assign to relevant agents

### Creating New Scenarios

1. Create JSON file in `src/scenarios/` directory
2. Define query and expectations
3. Run with: `uv run --env-file .env python -m src.runner src/scenarios/your_scenario.json`

## Mock Data

This demo uses mock financial data for testing purposes. In production:
- Replace `web_search_tool` with real search API (Google, Bing, etc.)
- Integrate with financial data providers (Bloomberg, Yahoo Finance, etc.)
- Add real-time market data sources

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure `OPENAI_API_KEY` is set in `.env` file
   - Use `unset VIRTUAL_ENV && uv run --env-file .env` to load environment variables

2. **Import Errors**
   - Run `uv sync` to install dependencies
   - Ensure you're in the correct directory

3. **Test Failures**
   - Check API key is valid
   - Ensure you're using compatible OpenAI models
   - Review scenario expectations match actual behavior
