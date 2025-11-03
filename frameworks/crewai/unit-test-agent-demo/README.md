# Unit Test Agent Demo - CrewAI

A CrewAI-based multi-agent system that automatically generates comprehensive unit test plans and pytest code for Python functions. Inspired by [Potpie's Unit Test Agent](https://github.com/potpie-ai/potpie).

## Overview

This demo showcases a three-agent workflow:
1. **Code Analyzer Agent**: Analyzes Python functions using AST parsing
2. **Test Planner Agent**: Creates structured test plans with scenarios
3. **Test Writer Agent**: Generates executable pytest code

## Features

- Analyzes Python code from GitHub repositories
- Extracts function signatures, parameters, and type hints via AST parsing
- Generates comprehensive test plans covering edge cases
- Creates pytest-compatible test code
- Supports simple functions, class methods, and complex scenarios

## Prerequisites

- Python 3.11 or higher
- OpenAI API key
- uv package manager

## Installation

1. Clone the repository and navigate to this demo:
```bash
cd frameworks/crewai/unit-test-agent-demo
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Add your OpenAI API key to `.env`:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

4. Install dependencies using uv:
```bash
unset VIRTUAL_ENV && uv sync
```

## Usage

### Run All Scenarios

```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner
```

### Run Specific Scenario

```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/simple_functions.json --verbose
```

### Run Tests

```bash
# Run all tests
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/ -v

# Run only unit tests
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/ -m unit -v

# Run with coverage
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/ --cov=src --cov-report=html
```

## Project Structure

```
unit-test-agent-demo/
├── src/
│   ├── agents.py          # CrewAI agent definitions
│   ├── tasks.py           # CrewAI task definitions
│   ├── crew.py            # Crew configuration
│   ├── tools.py           # Custom tools (AST parser, GitHub fetcher)
│   ├── context.py         # Configuration & Pydantic models
│   ├── runner.py          # Scenario execution engine
│   └── scenarios/         # JSON test scenarios
├── tests/                 # Comprehensive test suite
├── pyproject.toml         # Dependencies
└── README.md
```

## Scenario Examples

The demo includes three scenario types:

1. **Simple Functions**: Basic utilities (math, string manipulation)
2. **Class Methods**: Methods with state management
3. **Complex Cases**: Functions with external dependencies, mocks, async patterns

## How It Works

1. User provides a GitHub repository URL and target function
2. **Code Analyzer Agent** fetches and parses the Python code using AST
3. **Test Planner Agent** creates a structured test plan with scenarios
4. **Test Writer Agent** generates pytest code implementing the plan
5. Output includes both the test plan and executable test code

## Configuration

Edit `.env` to customize:

- `OPENAI_MODEL_NAME`: LLM model to use (default: gpt-4o)
- `MAX_ITERATIONS`: Maximum agent iterations (default: 10)
- `VERBOSE`: Enable detailed logging (default: true)

## Example Output

```python
# Generated test plan
{
  "function_name": "calculate_discount",
  "scenarios": [
    {"name": "valid_discount", "inputs": {...}, "expected": ...},
    {"name": "zero_discount", "inputs": {...}, "expected": ...},
    {"name": "invalid_percentage", "inputs": {...}, "expected": ...}
  ]
}

# Generated pytest code
def test_calculate_discount_valid():
    result = calculate_discount(100, 0.2)
    assert result == 80.0
```

## License

MIT License
