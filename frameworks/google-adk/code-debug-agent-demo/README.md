# Code Debug Agent Demo - Google ADK

An intelligent debugging assistant built with Google's Agent Development Kit (ADK) that helps developers resolve coding errors by searching Stack Exchange for proven solutions.

## Features

- **Error Analysis**: Automatically analyzes error messages to identify key components and search terms
- **Stack Exchange Integration**: Searches Stack Overflow and other Stack Exchange sites for relevant solutions
- **Multi-Language Support**: Handles errors from Python, JavaScript, TypeScript, Java, and more
- **Framework-Aware**: Recognizes framework-specific errors (React, Django, Node.js, etc.)
- **Solution Ranking**: Prioritizes accepted answers and highly-voted solutions
- **Comprehensive Tools**: Multiple specialized tools for different debugging scenarios

## Architecture

This agent follows Google ADK patterns and includes:

- **Debug Agent**: Main agent with comprehensive error analysis capabilities
- **Quick Debug Agent**: Streamlined agent for fast error lookups
- **Sequential Debug Agent**: Two-stage agent that analyzes then searches for solutions
- **Stack Exchange Service**: Async wrapper for Stack Exchange API integration
- **Scenario Runner**: Testing framework for validating agent behavior

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Google API key for Gemini models
- (Optional) Stack Exchange API key for higher rate limits

### Setup

```bash
# Install dependencies
unset VIRTUAL_ENV && uv sync
```

## Usage

### Running the Agent

#### Interactive Mode

Create a Python script (e.g., `run_agent.py`):

```python
import asyncio
from google.adk.runners import InMemoryRunner
from src.agents import debug_agent

async def main():
    runner = InMemoryRunner(agent=debug_agent, app_name="code-debug-agent")
    session = await runner.session_service.create_session(
        app_name="code-debug-agent",
        user_id="user123"
    )

    # Ask about an error
    async for event in runner.run_async(
        session_id=session.session_id,
        prompt="I'm getting ImportError: No module named 'pandas'"
    ):
        # Process response
        print(event)

asyncio.run(main())
```

Then run it with uv:

```bash
uv run python run_agent.py
```

#### Using the Runner Framework

```bash
# Run ALL scenario files in src/scenarios/
unset VIRTUAL_ENV && uv run python -m src.runner --all-scenarios

# Run all scenarios with a specific agent
unset VIRTUAL_ENV && uv run python -m src.runner --all-scenarios quick_debug_agent

# Run specific scenario file
unset VIRTUAL_ENV && uv run python -m src.runner src/scenarios/python_attribute_error_missing_method.json

# Use a specific agent with a specific scenario file
unset VIRTUAL_ENV && uv run python -m src.runner src/scenarios/python_attribute_error_missing_method.json quick_debug_agent

# List available agents
unset VIRTUAL_ENV && uv run python -m src.runner --list-agents
```

### Available Tools

1. **search_stack_exchange_for_error**
   - Searches for specific error messages
   - Extracts keywords intelligently
   - Returns solutions with context

2. **search_stack_exchange_general**
   - General programming queries
   - How-to questions and best practices
   - Filtered by tags and acceptance

3. **get_stack_exchange_answers**
   - Retrieves full answer content
   - Gets details for specific question IDs
   - Useful for deep dives into solutions

4. **analyze_error_and_suggest_fix**
   - Comprehensive error analysis
   - Suggests multiple fixes
   - Includes code context consideration

### Example Scenarios

The agent can handle various error types:

```python
# Python Import Errors
"ImportError: No module named 'requests'"

# JavaScript Type Errors
"TypeError: Cannot read property 'map' of undefined"

# TypeScript Compilation Errors
"Type 'string' is not assignable to type 'number'"

# Framework-Specific Errors
"React Hook 'useState' is called conditionally"
"django.db.migrations.exceptions.InconsistentMigrationHistory"

# CORS and Network Errors
"Access blocked by CORS policy"

# Version Control Issues
"CONFLICT (content): Merge conflict in app.js"
```

## Testing

### Unit Tests

```bash
# Run all tests
unset VIRTUAL_ENV && uv run pytest

# Run specific test
unset VIRTUAL_ENV && uv run pytest tests/test_agents.py::test_debug_agent
```

### Scenario Testing

Create custom scenarios in JSON format:

```json
{
  "scenarios": [
    {
      "name": "Custom Error Test",
      "description": "Test custom error handling",
      "error_message": "Your error message here",
      "programming_language": "python",
      "conversation": [
        {
          "user_input": "Error details",
          "expected_tools": ["search_stack_exchange_for_error"],
          "expected_keywords": ["solution", "fix"]
        }
      ]
    }
  ]
}
```

## Project Structure

```
code-debug-agent-demo/
├── src/
│   ├── __init__.py
│   ├── agents.py                 # Agent definitions
│   ├── tools.py                  # Stack Exchange tools
│   ├── prompts.py                # System prompts
│   ├── runner.py                 # Scenario runner
│   ├── services/
│   │   └── stackexchange_service.py  # API wrapper
│   └── scenarios/
│       └── common_errors.json    # Test scenarios
├── tests/
│   ├── conftest.py
│   └── test_agents.py
├── pyproject.toml
├── README.md
└── .env.example
```

## Configuration

### Environment Variables

- `GOOGLE_API_KEY`: Required for Gemini models
- `STACKEXCHANGE_API_KEY`: Optional, increases rate limits
- `GOOGLE_GENAI_USE_VERTEXAI`: Optional, use Vertex AI instead
- `DEBUG`: Enable debug logging

### Agent Models

The agents use Gemini 2.0 Flash by default. You can modify the model in `src/agents.py`:

```python
debug_agent = Agent(
    model='gemini-2.0-flash-exp',  # Change model here
    name='debug_agent',
    ...
)
```

## Advanced Usage

### Creating Custom Agents

```python
from google.adk import Agent
from src.tools import DEBUG_TOOLS

custom_agent = Agent(
    model='gemini-2.0-flash-exp',
    name='custom_debug_agent',
    instruction="Your custom instructions here",
    tools=DEBUG_TOOLS,
)
```

### Adding New Tools

```python
from google.adk.agents import Tool

async def custom_search_tool(query: str) -> str:
    # Your implementation
    return json.dumps(results)

custom_tool = Tool(
    function=custom_search_tool,
    name="custom_search",
    description="Description of what this tool does"
)
```

## Troubleshooting

### Common Issues

1. **Rate Limiting**: Add a Stack Exchange API key to increase limits
2. **No Results Found**: Try broadening search terms or using general search
3. **Timeout Errors**: Increase timeout in `StackExchangeService`
4. **API Key Issues**: Ensure your Google API key has Gemini access enabled

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is provided as a demonstration of Google ADK capabilities.

## Acknowledgments

- Built with [Google Agent Development Kit (ADK)](https://github.com/google/adk)
- Powered by Gemini models
- Integrates with Stack Exchange API
- Inspired by the ADK samples repository

## Related Resources

- [Google ADK Documentation](https://github.com/google/adk)
- [Stack Exchange API](https://api.stackexchange.com/)
- [ADK Samples](https://github.com/google/adk-samples)
- [LangChain Documentation](https://python.langchain.com/)