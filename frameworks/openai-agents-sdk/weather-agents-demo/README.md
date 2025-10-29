# OpenAI Agents SDK - Weather Agent Demo

A comprehensive demonstration of the OpenAI Agents SDK featuring a weather assistant agent with test-driven development approach.

## Overview

This project implements a weather assistant agent using the OpenAI Agents SDK. It demonstrates:
- **Weather information retrieval** using wttr.in API
- **Tool integration** for weather queries and comparisons
- **Context management** across conversation turns
- **Test-driven approach** with JSON-based scenarios
- **Contextual recommendations** based on weather conditions

## Architecture

### Agent
- **Weather Agent** - Provides weather information and recommendations for cities worldwide

### Tools
- `get_weather` - Get current weather for a specific city
- `compare_weather` - Compare weather between two cities

### Weather Service
- Integration with wttr.in API (free, no API key required)
- Simulated weather data for common cities
- Contextual weather recommendations

## Installation

1. Clone the repository and navigate to the project:
```bash
cd frameworks/openai-agents-sdk/weather-agents-demo
```

2. Install dependencies with uv:
```bash
unset VIRTUAL_ENV && uv sync --dev
```

## Usage

### Running Test Scenarios

Execute a single scenario:
```bash
uv run --env-file .env python -m src.runner src/scenarios/weather_queries.json --verbose
```

Run all scenarios:
```bash
for scenario in src/scenarios/*.json; do
    uv run --env-file .env python -m src.runner "$scenario" --verbose
done
```

### Running Tests with Pytest

Run all tests:
```bash
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/ -v
```

Run specific test categories:
```bash
# Unit tests only
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/test_agents.py::TestContext -v

# Integration tests (requires API key)
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/test_agents.py::TestIntegration -v

# Full scenario tests
unset VIRTUAL_ENV && RUN_FULL_SCENARIOS=1 uv run --env-file .env pytest tests/test_agents.py::TestIntegration::test_all_scenarios -v
```

### Scenario JSON Format

Scenarios are defined in JSON with the following structure:

```json
{
  "name": "Scenario Name",
  "description": "What this scenario tests",
  "initial_context": {},
  "conversation": [
    {
      "user": "What's the weather in San Francisco?",
      "expected": {
        "agent": "Weather Agent",
        "tools_called": ["get_weather"],
        "context_updates": ["current_location", "last_temperature"],
        "message_contains": ["San Francisco", "temperature"]
      }
    }
  ]
}
```

## Available Test Scenarios

1. **weather_queries.json** - Basic weather queries for different cities
2. **umbrella_recommendation.json** - Weather-based recommendations
3. **multi_location.json** - Comparing weather between cities

## Project Structure

```
weather-agents-demo/
├── src/
│   ├── __init__.py
│   ├── agents.py          # Agent definitions
│   ├── tools.py           # Tool implementations
│   ├── weather_service.py # Weather API integration
│   ├── context.py         # Context models
│   ├── runner.py          # Test scenario runner
│   └── scenarios/
│       ├── weather_queries.json
│       ├── umbrella_recommendation.json
│       └── multi_location.json
├── tests/
│   ├── __init__.py
│   ├── test_agents.py     # Comprehensive test suite
│   └── conftest.py        # Pytest fixtures
├── pyproject.toml
├── README.md
└── .env
```

## Key Features

### Weather Information
The agent can provide current weather for any city:
```
User: "What's the weather like in San Francisco?"
Agent: [Uses get_weather tool to fetch data]
       "Weather in San Francisco:
        Temperature: 62°F (17°C)
        Conditions: Partly cloudy with fog in the morning
        Recommendation: Great weather for outdoor activities! It's cool - consider a light jacket."
```

### Weather Comparisons
Compare weather between multiple cities:
```
User: "Compare the weather in Paris and Tokyo"
Agent: [Uses compare_weather tool]
       Provides temperature, conditions, and recommendations for both cities
```

### Context Preservation
Weather information and conversation state is maintained:
```python
context = WeatherAgentContext(
    current_location="San Francisco",
    last_temperature="62°F (17°C)",
    last_conditions="Partly cloudy",
    last_recommendation="Great weather for outdoor activities!"
)
```

### Test Validation
Each scenario turn can validate:
- Current agent
- Tools called
- Context updates
- Message content

## Example Execution

```bash
$ unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/weather_queries.json --verbose

============================================================
Running Scenario: Basic Weather Queries
Description: Test basic weather queries for different cities
============================================================

--- Turn 1 ---
🗣️  User: What's the weather like in San Francisco?
   Current Agent: Weather Agent
🔧 Tool Call: get_weather
   Tool Output: Weather in San Francisco:...
🤖 Weather Agent: The weather in San Francisco is currently 62°F (17°C) with partly cloudy conditions...
✅ Validation passed

--- Turn 2 ---
🗣️  User: How about New York?
   Current Agent: Weather Agent
🔧 Tool Call: get_weather
🤖 Weather Agent: In New York, it's 55°F (13°C) with overcast conditions and a chance of rain...
✅ Validation passed

============================================================
Scenario Complete: Basic Weather Queries
Result: ✅ PASSED
Successful turns: 3/3
Execution time: 3421ms
============================================================
```

## Development

### Adding New Tools

1. Create tool in `src/tools.py`:
```python
@function_tool(name_override="new_tool")
async def new_tool(context, param: str) -> str:
    # Tool logic
    return result
```

2. Add to weather agent in `src/agents.py`

### Creating New Scenarios

1. Create JSON file in `src/scenarios/` directory
2. Define conversation flow with expectations
3. Run with: `unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/your_scenario.json`

## Testing Best Practices

1. **Unit Tests**: Test individual components (tools, context, weather service)
2. **Integration Tests**: Test agent interactions with mocked weather API
3. **End-to-End Tests**: Run full scenarios with real API calls
4. **Mock Testing**: Use fixtures to mock external API calls

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `RUN_FULL_SCENARIOS` - Set to "1" to run full scenario tests with real API
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Weather Service

The project uses two weather data sources:
1. **Simulated Data**: Pre-defined data for common cities (San Francisco, New York, Tokyo, London, Paris)
2. **Live API**: wttr.in weather API as fallback (free, no API key required)

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure `OPENAI_API_KEY` is set in `.env` file
   - Run with: `unset VIRTUAL_ENV && uv run --env-file .env python ...`

2. **Import Errors**
   - Ensure all dependencies are installed: `unset VIRTUAL_ENV && uv sync --dev`
   - Check Python version: `>=3.9`

3. **Test Failures**
   - Check API key is valid
   - Ensure you're using compatible OpenAI models
   - Review scenario expectations match actual behavior

4. **Weather API Errors**
   - The project falls back to simulated data if live API fails
   - Check internet connectivity for live weather data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `unset VIRTUAL_ENV && uv run --env-file .env pytest tests/ -v`
5. Submit a pull request

## License

This project is provided as a demonstration of the OpenAI Agents SDK capabilities.

## Support

For issues and questions:
- Check the test output for detailed error messages
- Review scenario JSON for validation expectations
- Ensure environment variables are properly set
