# Open Deep Research Agents Demo

A multi-agent deep research system built with LangChain that autonomously conducts comprehensive research on complex topics. This implementation is inspired by the [open_deep_research](https://github.com/langchain-ai/open_deep_research) project and demonstrates advanced agent orchestration patterns.

## Overview

This system employs six specialized agents working in concert to conduct thorough research:

1. **Planner Agent** - Generates strategic search plans
2. **Search Agent** - Executes concurrent web searches
3. **Analyst Agent** - Analyzes and extracts insights
4. **Summarizer Agent** - Creates concise summaries
5. **Writer Agent** - Produces comprehensive reports
6. **Verifier Agent** - Validates research quality

## Architecture

```
User Query
    ↓
[Planner Agent] → Creates search strategy (3-5 search terms)
    ↓
[Search Agent] → Executes concurrent searches
    ↓
[Analyst Agent] → Extracts insights and patterns
    ↓
[Summarizer Agent] → Condenses information
    ↓
[Writer Agent] → Generates structured report
    ↓
[Verifier Agent] → Validates quality and completeness
    ↓
Final Research Report
```

## Features

- **Multi-Agent Orchestration**: Six specialized agents with distinct roles
- **Concurrent Search Execution**: Parallel search capabilities for efficiency
- **Comprehensive Analysis**: Deep insights extraction with confidence scoring
- **Quality Verification**: Built-in validation of research outputs
- **Flexible Configuration**: Support for multiple LLM providers
- **Scenario-Based Testing**: JSON-driven test scenarios for validation
- **Performance Tracking**: Detailed metrics and timing information
- **Mock Mode**: Full mock implementation for testing without API keys

## Installation

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Install dependencies using uv:
```bash
unset VIRTUAL_ENV && uv sync
```

### Required API Keys

- **OpenAI API Key** (required): For LLM capabilities
- **Tavily API Key** (optional): For web search (will use mock if not provided)

## Usage

### Command Line Interface

Run a research query directly:

```bash
# Run a simple research query
unset VIRTUAL_ENV && uv run --env-file .env python -m src.manager "What are the latest developments in quantum computing?"

# Run with specific research type
unset VIRTUAL_ENV && uv run --env-file .env python -m src.manager "Compare TensorFlow and PyTorch frameworks"
```

### Running Scenarios

Execute predefined research scenarios:

```bash
# Run a single scenario file
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/technology_research.json

# Run all scenarios in a directory
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/

# Run quietly (suppress verbose output)
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/ --quiet
```

### Python API

```python
import asyncio
from src.manager import ResearchManager
from src.context import ResearchType

async def main():
    # Create research manager
    manager = ResearchManager(verbose=True)

    # Conduct research
    context = await manager.conduct_research(
        query="What are the latest AI breakthroughs?",
        research_type=ResearchType.TECHNICAL,
        user_requirements={"depth": "comprehensive"}
    )

    # Access results
    print(context.full_report)
    print(f"Total results collected: {context.total_results_collected}")
    print(f"Verification score: {context.verification_result.accuracy_score:.2%}")

asyncio.run(main())
```

## Testing

### Run All Tests

```bash
# Run all tests
unset VIRTUAL_ENV && uv run pytest tests/ -v

# Run specific test file
unset VIRTUAL_ENV && uv run pytest tests/test_agents.py -v

# Run tests by marker
unset VIRTUAL_ENV && uv run pytest tests/ -m unit -v
```

### Test Categories

- **Unit Tests**: Test individual components
- **Integration Tests**: Test agent interactions
- **Scenario Tests**: End-to-end workflow validation

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | Required |
| `TAVILY_API_KEY` | Tavily API key for search | Optional |
| `DEFAULT_MODEL` | Default LLM model | gpt-4 |
| `PLANNER_MODEL` | Model for planning agent | gpt-4 |
| `SEARCH_MODEL` | Model for search agent | gpt-4 |
| `ANALYST_MODEL` | Model for analyst agent | gpt-4 |
| `SUMMARIZER_MODEL` | Model for summarizer agent | gpt-4 |
| `WRITER_MODEL` | Model for writer agent | gpt-4 |
| `VERIFIER_MODEL` | Model for verifier agent | gpt-4 |
| `MAX_SEARCH_RESULTS` | Max results per search | 5 |
| `MAX_SEARCH_ITERATIONS` | Max search iterations | 3 |
| `MAX_CONCURRENT_SEARCHES` | Max parallel searches | 3 |
| `VERBOSE` | Enable verbose output | true |
| `USE_MOCK_TOOLS` | Use mock implementations | false |

### Research Types

The system supports different research types:

- `GENERAL` - General purpose research
- `TECHNICAL` - Technology and engineering topics
- `SCIENTIFIC` - Scientific research and studies
- `MARKET` - Market analysis and business
- `HISTORICAL` - Historical events and analysis
- `COMPARATIVE` - Comparative studies and analysis

## Scenario Format

Create custom research scenarios in JSON:

```json
{
  "name": "Scenario Name",
  "description": "Scenario description",
  "query": "Research query text",
  "user_requirements": {
    "depth": "comprehensive",
    "focus": "specific_area"
  },
  "expectations": {
    "min_search_terms": 3,
    "min_report_length": 500,
    "required_sections": ["Executive Summary", "Key Findings"],
    "verification_should_pass": true,
    "required_keywords": ["keyword1", "keyword2"]
  },
  "metadata": {
    "research_type": "technical",
    "priority": "high",
    "test_type": "comprehensive"
  }
}
```

## Project Structure

```
open-deep-research-agents-demo/
├── src/
│   ├── __init__.py
│   ├── agents.py          # Six specialized research agents
│   ├── context.py         # ResearchContext data model
│   ├── tools.py           # Research tools (search, analysis, etc.)
│   ├── manager.py         # Orchestration manager
│   ├── runner.py          # Scenario execution engine
│   └── scenarios/         # JSON test scenarios
│       ├── technology_research.json
│       ├── scientific_study.json
│       ├── market_analysis.json
│       ├── historical_research.json
│       └── comparative_study.json
├── tests/
│   ├── conftest.py        # Pytest fixtures
│   ├── test_agents.py     # Agent tests
│   ├── test_context.py    # Context model tests
│   ├── test_tools.py      # Tool tests
│   └── test_manager.py    # Manager tests
├── pyproject.toml         # Project configuration
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Key Components

### ResearchContext

Central state management for the research workflow:

- Query and requirements tracking
- Search plan and results storage
- Analysis findings and insights
- Report sections and verification
- Workflow stage management
- Error and warning collection

### Agent Responsibilities

| Agent | Responsibilities | Tools Used |
|-------|-----------------|------------|
| **Planner** | Create search strategy, identify key concepts | None |
| **Search** | Execute web searches, collect results | web_search, concurrent_search |
| **Analyst** | Extract insights, identify patterns | analysis_tool |
| **Summarizer** | Create concise summaries | summary_tool |
| **Writer** | Generate comprehensive reports | None |
| **Verifier** | Validate quality and accuracy | verification_tool |

### Workflow Stages

1. `INITIAL` - Starting state
2. `PLANNING` - Creating search strategy
3. `SEARCHING` - Collecting information
4. `ANALYZING` - Extracting insights
5. `SUMMARIZING` - Condensing information
6. `WRITING` - Generating report
7. `VERIFYING` - Quality validation
8. `COMPLETE` - Successfully finished
9. `ERROR` - Error occurred

## Performance Metrics

The system tracks various performance metrics:

- **Execution Time**: Per stage and total
- **Search Metrics**: Terms used, results collected
- **Quality Scores**: Accuracy, completeness, consistency
- **Report Metrics**: Length, sections, references

## Extending the System

### Adding New Agents

1. Create agent class inheriting from `ResearchAgent`
2. Define system prompt and tools
3. Implement specialized methods
4. Register in `AGENTS` dictionary

### Adding New Tools

1. Create tool function with `@tool` decorator
2. Define input/output schemas
3. Implement tool logic
4. Register in `AVAILABLE_TOOLS`

### Custom Scenarios

1. Create JSON file in `src/scenarios/`
2. Define query and expectations
3. Run with scenario runner

## Comparison with Reference Implementations

This implementation draws inspiration from:

- **OpenAI Agents SDK**: Multi-agent orchestration patterns
- **Google ADK**: Tool integration and testing strategies
- **LangChain Open Deep Research**: Core research workflow

### Key Differences

- Uses LangGraph's `create_react_agent` for agent management
- Implements comprehensive testing with pytest
- Provides mock implementations for all external services
- Includes detailed performance tracking and metrics
- Supports multiple research types with specialized handling

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure `.env` file contains valid API keys
2. **Import Errors**: Run `uv sync` to install dependencies
3. **Async Errors**: Use Python 3.9+ with asyncio support
4. **Memory Issues**: Reduce `MAX_CONCURRENT_SEARCHES` for limited resources

### Debug Mode

Enable detailed logging:

```bash
export VERBOSE=true
export USE_MOCK_TOOLS=true  # Use mock implementations
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is for demonstration and educational purposes.

## Acknowledgments

- [LangChain](https://langchain.com/) for the agent framework
- [OpenAI](https://openai.com/) for LLM capabilities
- [Tavily](https://tavily.com/) for search API
- Inspired by the open_deep_research project