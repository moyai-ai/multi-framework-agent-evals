# Static Code Analysis Agent Demo with Langfuse Observability

A LangGraph ReAct agent that performs static code analysis on GitHub repositories using OpenGrep and GitHub MCP integration, **instrumented with Langfuse for full observability**.

> 🔍 **This is the traced version** of the static code analysis agent. For the untraced version, see `frameworks/langchain/static-code-analysis-agent-demo/`.

## Overview

This demo showcases a **ReAct (Reasoning + Acting)** agent built with LangGraph that can:
- Analyze code repositories for security vulnerabilities
- Detect code quality issues and anti-patterns
- Identify vulnerable dependencies
- Generate detailed reports with remediation recommendations
- **📊 Provide full observability via Langfuse tracing**

The agent uses the ReAct pattern to iteratively reason about what analysis to perform, execute tools, observe results, and continue until the analysis is complete. **All operations are traced in Langfuse** for comprehensive monitoring and debugging.

## 🆕 Langfuse Integration

This version includes full Langfuse tracing for:
- **LLM Calls**: Track all OpenAI API calls with prompts, responses, tokens, and costs
- **Tool Executions**: Monitor GitHub MCP tools and OpenGrep analysis
- **Agent Workflow**: Visualize the complete ReAct loop
- **Node-level Spans**: Detailed timing and data for each graph node
- **End-to-end Traces**: Complete analysis sessions grouped under unified traces

**See [LANGFUSE_README.md](./LANGFUSE_README.md) for detailed Langfuse integration documentation.**

## Features

### 🔒 Security Analysis
- SQL Injection detection
- Cross-Site Scripting (XSS) vulnerabilities
- Hardcoded secrets and API keys
- Command injection risks
- Insecure deserialization

### 📊 Code Quality Analysis
- Long functions and methods
- Deep nesting and complexity
- Empty exception handlers
- Magic numbers and TODO comments
- Code duplication

### 📦 Dependency Analysis
- Known CVE vulnerabilities
- Outdated packages
- License compliance
- Deprecated dependencies

## Architecture

```
┌─────────────────┐
│  LangGraph      │
│  ReAct Agent    │
└────────┬────────┘
         │
    ┌────▼────┐
    │Reasoning│◄──┐
    └────┬────┘   │
         │        │
    ┌────▼────┐   │
    │ Action  │   │
    └────┬────┘   │
         │        │
    ┌────▼─────┐  │
    │Observation├─┘
    └──────────┘
         │
    ┌────▼────┐
    │ Report  │
    └─────────┘
```

### Components

- **Agent**: LangGraph ReAct implementation with state management
- **Tools**: GitHub MCP integration, OpenGrep analysis, dependency checking
- **Scenarios**: Pre-defined test scenarios for security, quality, and dependencies
- **Runner**: Scenario execution and validation framework

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Install dependencies using uv:
```bash
unset VIRTUAL_ENV && uv sync
```

2. (Recommended) Install OpenGrep for real static analysis:
```bash
# Install OpenGrep
curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash

# Verify installation
opengrep --version
```

### Required API Keys

- **OpenAI API Key** (required): For LLM capabilities
- **Langfuse API Keys** (required for tracing): Get free keys at [cloud.langfuse.com](https://cloud.langfuse.com)

### Langfuse Setup

1. Sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. Create a new project
3. Go to **Settings** → **API Keys**
4. Copy your **Public Key** (starts with `pk-lf-`) and **Secret Key** (starts with `sk-lf-`)
5. Add them to your `.env` file:

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_ENABLED=true
```

### OpenGrep Configuration

This demo supports both **real OpenGrep analysis** and **mock analysis**:

- **Unit Tests**: Automatically use mock OpenGrep (no installation needed)
- **Scenarios**: Use real OpenGrep by default for accurate results
- **Fallback**: If OpenGrep is not installed, automatically falls back to mock analysis

To force mock mode (useful for development without OpenGrep):
```bash
export USE_MOCK_OPENGREP=true
```

## Usage

### Command Line Interface

Run a static analysis directly:

```bash
# Run a security analysis on a repository
unset VIRTUAL_ENV && uv run --env-file .env python -m src.manager "https://github.com/example/repo"

# Run with specific analysis type
unset VIRTUAL_ENV && uv run --env-file .env python -m src.manager "https://github.com/example/repo" --type quality

# Run with specific analysis type (choices: security, quality, dependencies)
unset VIRTUAL_ENV && uv run --env-file .env python -m src.manager "https://github.com/example/repo" --type dependencies
```

### Running Scenarios

Execute predefined analysis scenarios with real OpenGrep:

```bash
# Run all scenarios in the src/scenarios directory (recommended)
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner --all-scenarios

# Run a single scenario file (uses real OpenGrep if installed)
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/security_vulnerabilities.json

# Run all scenarios in a directory
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/

# Run quietly (suppress verbose output)
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner --all-scenarios --quiet

# Run with mock OpenGrep (if OpenGrep not installed or for testing)
USE_MOCK_OPENGREP=true unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner --all-scenarios
```

**OpenGrep Behavior:**
- If OpenGrep is installed: Uses real analysis for accurate results
- If OpenGrep is not found: Automatically falls back to mock analysis with warning
- To force mock mode: Set `USE_MOCK_OPENGREP=true`

### Python API

```python
import asyncio
from src.manager import AnalysisManager

async def main():
    # Create analysis manager
    manager = AnalysisManager(verbose=True)

    # Conduct analysis
    result = await manager.analyze_repository(
        repository_url="https://github.com/example/repo",
        analysis_type="security",  # or "quality", "dependencies"
    )

    # Access results
    print(f"Repository: {result['repository']}")
    print(f"Files Analyzed: {len(result['files_analyzed'])}")
    print(f"Issues Found: {len(result['issues_found'])}")
    print(f"Report: {result['final_report']}")

asyncio.run(main())
```

## Testing

### Run All Tests

```bash
# Run all tests (automatically uses mock OpenGrep)
unset VIRTUAL_ENV && uv run pytest

# Run with verbose output
unset VIRTUAL_ENV && uv run pytest -v

# Run specific test file
unset VIRTUAL_ENV && uv run pytest tests/test_agent.py -v

# Run only unit tests (agent tests, fast)
unset VIRTUAL_ENV && uv run pytest -m unit -v

# Run only scenario tests (slower, tests scenario execution)
unset VIRTUAL_ENV && uv run pytest -m scenario -v
```

### Test Categories

- **Unit Tests** (`-m unit`): Test individual agent components (uses mock OpenGrep automatically)
  - Agent state management
  - Agent creation and configuration
  - Agent workflow and execution
  - Prompt formatting
- **Scenario Tests** (`-m scenario`): Test scenario execution and validation (slower)
  - Scenario loading and structure
  - Scenario execution with mocked analysis
  - Expectation validation
  - Results handling and reporting

**Note:** All tests automatically use mock OpenGrep regardless of your environment settings. This is configured in `tests/conftest.py` to ensure tests run quickly and don't require external tools.

## Scenario Format

Create custom analysis scenarios in JSON:

```json
{
  "name": "Scenario Name",
  "description": "Scenario description",
  "initial_context": {
    "repository_url": "https://github.com/example/repo",
    "analysis_type": "security"
  },
  "conversation": [
    {
      "user": "User input",
      "expected": {
        "findings": ["expected-issue-types"],
        "message_contains": ["keywords"],
        "severity_contains": ["HIGH", "CRITICAL"]
      }
    }
  ],
  "metadata": {
    "test_type": "security",
    "priority": "high"
  }
}
```

## Project Structure

```
static-code-analysis-agent-demo/
├── src/
│   ├── __init__.py
│   ├── agent/              # LangGraph ReAct agent
│   │   ├── graph.py        # Agent workflow
│   │   ├── state.py        # State management
│   │   └── prompts.py      # System prompts
│   ├── tools/              # Analysis tools
│   │   ├── github_tools.py    # GitHub MCP integration
│   │   ├── opengrep_tools.py  # OpenGrep analysis
│   │   └── analysis_tools.py  # Result processing
│   ├── scenarios/          # JSON test scenarios
│   │   ├── security_vulnerabilities.json
│   │   ├── code_quality_analysis.json
│   │   └── dependency_analysis.json
│   ├── context.py          # Configuration
│   ├── manager.py          # Orchestration manager
│   └── runner.py           # Scenario execution engine
├── tests/
│   ├── conftest.py         # Pytest fixtures
│   ├── test_agent.py       # Agent tests
│   └── test_tools.py       # Tool tests
├── pyproject.toml          # Project configuration
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | Required |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key | Required for tracing |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key | Required for tracing |
| `LANGFUSE_HOST` | Langfuse host URL | https://cloud.langfuse.com |
| `LANGFUSE_ENABLED` | Enable/disable Langfuse tracing | true |
| `MODEL_NAME` | LLM model to use | gpt-4-turbo-preview |
| `TEMPERATURE` | Model temperature | 0.3 |
| `DEBUG` | Enable debug output | false |
| `LOG_LEVEL` | Logging level | INFO |
| `USE_MOCK_OPENGREP` | Force mock OpenGrep (true/false) | false |
| `OPENGREP_PATH` | Path to opengrep binary | opengrep |

### Analysis Types

The system supports different analysis types:

- `security` - Security vulnerability detection
- `quality` - Code quality and maintainability analysis
- `dependencies` - Dependency and CVE analysis

## How It Works

1. **Initialization**: The agent receives a repository URL and analysis type
2. **Reasoning**: Determines what files to analyze and which tools to use
3. **Action**: Executes tools (fetch files, run OpenGrep, check dependencies)
4. **Observation**: Processes results and updates state
5. **Iteration**: Repeats until analysis is complete or max steps reached
6. **Reporting**: Generates comprehensive report with findings and recommendations

## Extending the System

### Adding New Analysis Rules

Create custom OpenGrep rules in `src/tools/opengrep_tools.py`:

```python
# Add to the OpenGrepAnalyzer class
def add_custom_rule(self, rule_id: str, pattern: str, message: str, severity: str):
    """Add a custom analysis rule."""
    rule = {
        "id": rule_id,
        "pattern": pattern,
        "message": message,
        "severity": severity,
    }
    self.custom_rules.append(rule)
```

### Custom Scenarios

1. Create JSON file in `src/scenarios/`
2. Define repository URL and analysis type
3. Specify expected findings and validations
4. Run with scenario runner

Example scenario structure provided in Scenario Format section above.

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure `.env` file contains valid OpenAI API key
2. **Import Errors**: Run `unset VIRTUAL_ENV && uv sync` to install dependencies
3. **Async Errors**: Use Python 3.9+ with asyncio support
4. **Scenario Not Found**: Check scenario name matches exactly (case-insensitive)
5. **OpenGrep Not Found**: Install OpenGrep or set `USE_MOCK_OPENGREP=true`

### OpenGrep Installation Issues

If you see "Warning: OpenGrep not found":

```bash
# Option 1: Install OpenGrep for real analysis
curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash

# Option 2: Use mock mode (good for development/testing)
export USE_MOCK_OPENGREP=true

# Option 3: Specify custom OpenGrep path
export OPENGREP_PATH=/path/to/opengrep
```

### Debug Mode

Enable detailed logging:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## Key Components

### AnalysisManager

Central management for running static code analysis:

- Repository URL validation
- Analysis type configuration
- Result aggregation and reporting
- Error handling and logging

### Agent Workflow

The ReAct agent follows this pattern:

1. **Reasoning**: Determines what files to analyze and which tools to use
2. **Action**: Executes tools (fetch files, run OpenGrep, check dependencies)
3. **Observation**: Processes results and updates state
4. **Iteration**: Repeats until analysis is complete or max steps reached
5. **Reporting**: Generates comprehensive report with findings

### Performance Metrics

- Average analysis time: 30-60 seconds per repository
- Max steps limit: 20 (configurable)
- File size limit: 500KB per file
- Max files per analysis: 50

## License

This is a demonstration project for educational purposes.

## Comparison with Reference Implementations

This implementation draws inspiration from:

- **LangGraph**: ReAct pattern for agent orchestration
- **OpenGrep**: Pattern-based static analysis
- **LangChain**: Tool integration and LLM chaining

### Key Features

- Uses LangGraph's StateGraph for agent management
- Implements comprehensive testing with pytest
- Provides mock implementations for external tools
- Includes detailed scenario-based validation
- Supports multiple analysis types

## Acknowledgments

- LangGraph for the graph-based agent framework
- OpenGrep for static analysis capabilities
- GitHub MCP for repository integration