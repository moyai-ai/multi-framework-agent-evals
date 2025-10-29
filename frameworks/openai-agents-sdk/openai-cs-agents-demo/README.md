# OpenAI Agents SDK - Airline Customer Service Demo

A comprehensive demonstration of the OpenAI Agents SDK featuring a multi-agent airline customer service system with test-driven development approach.

## Overview

This project implements a full airline customer service agent system using the OpenAI Agents SDK. It demonstrates:
- **Multi-agent orchestration** with intelligent handoffs
- **Tool integration** for performing actions
- **Context management** across agent transitions
- **Input guardrails** for safety and relevance
- **Test-driven approach** with JSON-based scenarios

## Architecture

### 5 Specialized Agents

1. **Triage Agent** - Entry point that routes requests to specialists
2. **Seat Booking Agent** - Handles seat changes and selection
3. **Flight Status Agent** - Provides flight status and gate information
4. **FAQ Agent** - Answers general policy questions
5. **Cancellation Agent** - Processes flight cancellations

### 6 Function Tools

- `faq_lookup_tool` - Answer frequently asked questions
- `update_seat` - Change seat assignments
- `flight_status_tool` - Check flight status
- `baggage_tool` - Provide baggage information
- `display_seat_map` - Trigger seat map display
- `cancel_flight` - Process cancellations

### 2 Guardrails

- **Relevance Guardrail** - Ensures conversations stay airline-related
- **Jailbreak Guardrail** - Detects prompt injection attempts

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd openai-cs-agents-demo/src
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or sync with uv:
```bash
unset VIRTUAL_ENV && uv sync
```

3. Set up your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add your API key
```

## Usage

### Running Test Scenarios

Execute a single scenario:
```bash
uv run --env-file .env python -m src.runner scenarios/seat_change.json --verbose
```

Run all scenarios:
```bash
for scenario in scenarios/*.json; do
    uv run --env-file .env python -m src.runner "$scenario" --verbose
done
```

### Running Tests with Pytest

Run all tests:
```bash
pytest tests/ -v
```

Run specific test categories:
```bash
# Unit tests only
pytest tests/test_agents.py::TestContext -v

# Integration tests (requires API key)
OPENAI_API_KEY=your-key pytest tests/test_agents.py::TestIntegration -v

# Full scenario tests
RUN_FULL_SCENARIOS=1 pytest tests/test_agents.py::TestIntegration::test_full_scenarios -v
```

### Scenario JSON Format

Scenarios are defined in JSON with the following structure:

```json
{
  "name": "Scenario Name",
  "description": "What this scenario tests",
  "initial_context": {
    "passenger_name": "John Doe",
    "flight_number": "UA123"
  },
  "conversation": [
    {
      "user": "User input message",
      "expected": {
        "agent": "Expected Agent Name",
        "handoffs": ["Agent A -> Agent B"],
        "tools_called": ["tool_name"],
        "context_updates": ["field_name"],
        "message_contains": ["expected", "keywords"]
      }
    }
  ]
}
```

## Available Test Scenarios

1. **seat_change.json** - Complete seat change flow with handoffs
2. **flight_status.json** - Flight status inquiry and updates
3. **cancellation.json** - Flight cancellation with refund info
4. **faq_queries.json** - Various FAQ interactions
5. **handoff_demo.json** - Complex multi-agent handoff showcase

## Project Structure

```
openai-cs-agents-demo/
├── src/
│   ├── __init__.py
│   ├── agents.py          # Agent definitions
│   ├── tools.py           # Tool implementations
│   ├── guardrails.py      # Guardrail definitions
│   ├── context.py         # Context models
│   └── runner.py          # Test scenario runner
├── tests/
│   ├── __init__.py
│   ├── test_agents.py     # Comprehensive test suite
│   └── conftest.py        # Pytest fixtures
├── scenarios/
│   ├── seat_change.json
│   ├── flight_status.json
│   ├── cancellation.json
│   ├── faq_queries.json
│   └── handoff_demo.json
├── requirements.txt
├── README.md
└── .env.example
```

## Key Features

### Multi-Agent Handoffs
Agents can seamlessly transfer conversations to specialists based on customer needs:
```python
# Triage agent hands off to Seat Booking Agent
handoff(agent=seat_booking_agent, on_handoff=on_seat_booking_handoff)
```

### Context Preservation
Customer information and conversation state is maintained across handoffs:
```python
context = AirlineAgentContext(
    passenger_name="John Smith",
    confirmation_number="ABC123",
    flight_number="UA456",
    seat_number="12A"
)
```

### Tool Integration
Agents use tools to perform real actions:
```python
@function_tool(name_override="update_seat")
async def update_seat(context, confirmation_number, new_seat):
    # Update seat assignment
    return f"Seat updated to {new_seat}"
```

### Test Validation
Each scenario turn can validate:
- Current agent
- Handoffs performed
- Tools called
- Context updates
- Message content

## Example Execution

```bash
$ uv run --env-file .env python -m src.runner scenarios/seat_change.json --verbose

============================================================
Running Scenario: Seat Change Scenario
Description: Test complete seat change flow with handoff from triage to seat booking agent
============================================================

--- Turn 1 ---
🗣️ User: Hi, I need to change my seat on my upcoming flight
   Current Agent: Triage Agent
🤖 Triage Agent: I'll connect you with our Seat Booking specialist right away.
🔄 Handoff: Triage Agent -> Seat Booking Agent
✅ Validation passed

--- Turn 2 ---
🗣️ User: My confirmation number is ABC123
   Current Agent: Seat Booking Agent
🤖 Seat Booking Agent: I have your confirmation. What seat would you like?
✅ Validation passed

[... continues ...]

============================================================
Scenario Complete: Seat Change Scenario
Result: ✅ PASSED
Successful turns: 5/5
Execution time: 4523ms
============================================================
```

## Performance Metrics

The test runner tracks:
- Execution time per turn
- Total scenario execution time
- Agent response times
- Tool execution times
- Handoff transition times

## Development

### Adding New Agents

1. Define the agent in `src/agents.py`:
```python
new_agent = Agent[AirlineAgentContext](
    name="New Agent",
    model="gpt-4o",
    instructions="Agent instructions...",
    tools=[tool1, tool2],
    handoffs=[other_agent]
)
```

2. Add to AGENTS registry:
```python
AGENTS["new_agent"] = new_agent
```

### Adding New Tools

1. Create tool in `src/tools.py`:
```python
@function_tool(name_override="tool_name")
async def tool_name(param1: str) -> str:
    # Tool logic
    return result
```

2. Assign to relevant agents

### Creating New Scenarios

1. Create JSON file in `scenarios/` directory
2. Define conversation flow with expectations
3. Run with: `uv run --env-file .env python -m src.runner scenarios/your_scenario.json`

## Testing Best Practices

1. **Unit Tests**: Test individual components (tools, context, agents)
2. **Integration Tests**: Test agent interactions with mocked API
3. **End-to-End Tests**: Run full scenarios with real API calls
4. **Performance Tests**: Ensure response times meet thresholds

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `RUN_FULL_SCENARIOS` - Set to "1" to run full scenario tests
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure `OPENAI_API_KEY` is set in environment or `.env` file

2. **Import Errors**
   - Run from the `src` directory
   - Ensure all dependencies are installed

3. **Test Failures**
   - Check API key is valid
   - Ensure you're using compatible OpenAI models
   - Review scenario expectations match actual behavior

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is provided as a demonstration of the OpenAI Agents SDK capabilities.

## Support

For issues and questions:
- Check the test output for detailed error messages
- Review scenario JSON for validation expectations
- Ensure guardrails aren't blocking legitimate requests