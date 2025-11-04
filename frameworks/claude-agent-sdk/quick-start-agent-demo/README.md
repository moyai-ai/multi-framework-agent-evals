# Claude Agent SDK Quick Start Demo

This demo showcases the three main usage patterns from the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) quick start guide:

1. **Basic Query** - Simple question/answer interaction
2. **Query with Options** - Custom configuration (system prompt, max turns)
3. **Query with Tools** - File operations using built-in tools (Read, Write)

## Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key

## Setup

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Navigate to the project directory**:
   ```bash
   cd frameworks/claude-agent-sdk/quick-start-demo
   ```

3. **Configure your API key**:

   Edit the `.env` file and add your Anthropic API key:
   ```bash
   ANTHROPIC_API_KEY=your_actual_api_key_here
   ```

4. **Install dependencies**:
   ```bash
   unset VIRTUAL_ENV && uv sync
   ```

## Running the Demo

Run all three examples:

```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.main
```

## Running Tests

Run the test suite:

```bash
unset VIRTUAL_ENV && uv run pytest
```

Run tests with verbose output:

```bash
unset VIRTUAL_ENV && uv run pytest -v
```

### Test Structure

The test suite includes:
- **Unit tests**: Test individual examples
- **Scenario tests**: Test using JSON scenario definitions
- **Integration tests**: Test actual API calls with streaming responses

## Project Structure

```
quick-start-agent-demo/
├── pyproject.toml              # Project dependencies and configuration
├── .env                        # API key configuration
├── README.md                   # This file
├── src/
│   ├── __init__.py
│   ├── main.py                # Main demo with three examples
│   └── scenarios/
│       ├── __init__.py
│       └── ....json           # Test scenarios
└── tests/
    ├── __init__.py
    ├── conftest.py            # Pytest fixtures
    └── test_unit.py           # Test suite
```

## Key Features Demonstrated

### 1. Basic Query
Simple interaction with the Claude agent without any custom configuration.

```python
from claude_agent_sdk import query

async for message in query(prompt="What is 2 + 2?"):
    # Process streaming messages
    pass
```

### 2. Custom Options
Configure the agent with system prompts and turn limits.

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    system_prompt="You are a helpful math tutor.",
    max_turns=1
)

async for message in query(prompt="What is 2 + 2?", options=options):
    # Process messages with custom configuration
    pass
```

### 3. Tool Usage
Use built-in tools like Read and Write for file operations.

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write"],
    max_turns=5
)

async for message in query(prompt="Create and read a file", options=options):
    # Process messages that may include tool usage
    pass
```

## Scenarios

Test scenarios are defined in JSON format and can be found in [src/scenarios/quick_start_scenarios.json](src/scenarios/quick_start_scenarios.json).

Each scenario includes:
- **name**: Descriptive name for the test
- **description**: What the scenario tests
- **prompt**: The user query
- **options**: Optional configuration (system prompt, tools, max turns)
- **expected**: Validation criteria (message content, tools used)

Example scenario:

```json
{
  "name": "Basic Query - Math",
  "description": "Test basic query without options",
  "prompt": "What is 2 + 2?",
  "options": null,
  "expected": {
    "message_contains": ["4"],
    "has_text_response": true,
    "tools_called": []
  }
}
```

## Dependencies

- **claude-agent-sdk**: Core Claude Agent SDK
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support

## Troubleshooting

### API Key Not Set

If you see:
```
Please set ANTHROPIC_API_KEY in .env file
```

Make sure you've edited the `.env` file and replaced `your_api_key_here` with your actual Anthropic API key.

### Import Errors

If you encounter import errors, ensure dependencies are installed:
```bash
uv sync
```

### Tests Skipped

If tests are skipped due to missing API key, configure the `.env` file with a valid API key.

## Additional Resources

- [Claude Agent SDK Documentation](https://github.com/anthropics/claude-agent-sdk-python)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [uv Documentation](https://docs.astral.sh/uv/)
