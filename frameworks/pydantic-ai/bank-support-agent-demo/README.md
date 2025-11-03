# Pydantic AI - Bank Support Agent Demo

A comprehensive demonstration of a bank support agent system built with the Pydantic AI framework, showcasing tool integration, context management, and multi-agent orchestration for banking operations.

## Overview

This demo implements a sophisticated bank support system with the following capabilities:
- Secure customer authentication
- Account balance inquiries
- Transaction history retrieval
- Fund transfers between accounts
- Support ticket creation
- Fraud alert monitoring
- Contact information updates

## Architecture

### Agent System

The demo features three specialized agents that work together:

1. **Bank Support Agent** - Main entry point handling general customer inquiries
2. **Fraud Specialist Agent** - Handles fraud detection and security concerns
3. **Account Specialist Agent** - Manages account operations and transactions

### Data Flow

```
User Request → Agent Selection → Tool Execution → Context Update → Response
                    ↓                  ↓              ↓
            (Based on request)  (Database ops)  (State tracking)
```

### Key Components

- **Context Management**: Pydantic models track conversation state and customer data
- **Tool System**: Async functions for database operations and business logic
- **Agent Registry**: Dynamic agent selection based on request type
- **Scenario Runner**: JSON-based testing framework for validation

## Installation

### Prerequisites

- Python 3.12+
- uv package manager
- OpenAI API key (or compatible LLM provider)

### Setup

1. Install dependencies using uv:
```bash
unset VIRTUAL_ENV && uv sync --dev
```

2. Add your OpenAI API key to `.env`:
```env
OPENAI_API_KEY=your-api-key-here
```

3. Initialize the database:
```bash
uv run python -m src.database_init
```

## Usage

### Running Test Scenarios

Execute a single scenario:
```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/authentication_flow.json -v
```

Run all scenarios in the directory:
```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/ -v
```

### Running Tests

Run all tests:
```bash
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/ -v
```

Run specific test categories:
```bash
# Unit tests only
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/ -m unit

# Integration tests
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/ -m integration

# Scenario tests
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/ -m scenario
```

### Example Output

```
Running Scenario: Authentication Flow
A test of customer authentication and basic account inquiry

Turn 1: Hi, I need to check my account balance
Response: Hello! I'd be happy to help you check your account balance. For security purposes, I'll need to verify your identity first. Could you please provide your email address and the last 4 digits of your SSN?

Turn 2: My email is test@example.com and the last 4 of my SSN is 1234
Response: Successfully authenticated. Welcome back, Test User!
Tools used: authenticate_customer

Turn 3: Now can you show me my account balances?
Response: Here are your current account balances:
- Checking Account (...7890): $1,500.00
- Savings Account (...4321): $5,000.00

Total Balance: $6,500.00
Tools used: get_account_balance

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         Scenario Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│ Metric              │ Value   │
│ Total Turns         │ 3       │
│ Total Tools Called  │ 2       │
│ Total Errors        │ 0       │
│ Average Turn Time   │ 1.234s  │
│ Final Authenticated │ True    │
│ Successful Turns    │ 3       │
│ Failed Turns        │ 0       │
│ Total Time          │ 3.70s   │
│ Status              │ PASSED  │
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Project Structure

```
pydantic-ai/
├── pyproject.toml              # Project configuration and dependencies
├── README.md                   # This documentation
├── .python-version            # Python version specification (3.12)
├── .env.example               # Environment variables template
├── src/
│   ├── __init__.py
│   ├── agents.py              # Agent definitions and registry
│   ├── context.py             # Pydantic models for state management
│   ├── tools.py               # Bank operation tools
│   ├── runner.py              # Scenario execution framework
│   ├── database_init.py       # Database setup script
│   ├── scenarios/             # JSON test scenarios
│   │   ├── authentication_flow.json
│   │   ├── fund_transfer.json
│   │   ├── transaction_history.json
│   │   ├── support_ticket.json
│   │   └── update_contact_info.json
│   └── data/
│       └── bank_support.db    # SQLite database
└── tests/
    ├── __init__.py
    ├── conftest.py            # Pytest fixtures
    ├── test_context.py        # Context model tests
    ├── test_agents.py         # Agent tests
    ├── test_tools.py          # Tool tests
    └── test_runner.py         # Runner tests
```

## Available Agents

### Bank Support Agent
- **Key**: `bank_support`
- **Description**: Main customer service agent handling general inquiries
- **Tools**: All available tools
- **Use Cases**: Initial customer contact, general questions, routing

### Fraud Specialist Agent
- **Key**: `fraud_specialist`
- **Description**: Specialized agent for fraud detection and security
- **Tools**: authenticate_customer, check_fraud_alert, get_recent_transactions, create_support_ticket
- **Use Cases**: Suspicious activity, unauthorized transactions, security concerns

### Account Specialist Agent
- **Key**: `account_specialist`
- **Description**: Handles account management and transactions
- **Tools**: authenticate_customer, get_account_balance, get_recent_transactions, transfer_funds, update_contact_info
- **Use Cases**: Balance inquiries, fund transfers, account updates

## Tools

### Authentication & Security
- `authenticate_customer`: Verify customer identity with email and SSN
- `check_fraud_alert`: Check for active fraud alerts on accounts

### Account Operations
- `get_account_balance`: Retrieve balance for all or specific accounts
- `get_recent_transactions`: Get transaction history with filtering options
- `transfer_funds`: Transfer money between customer accounts

### Customer Service
- `create_support_ticket`: Create support tickets for complex issues
- `update_contact_info`: Update customer email or phone number

## Configuration

### Environment Variables

```env
# Required
OPENAI_API_KEY=your-api-key-here

# Optional
DEFAULT_MODEL=gpt-4o            # LLM model to use
DEFAULT_TEMPERATURE=0.3         # Model temperature
DATABASE_PATH=src/data/bank_support.db  # Database location
LOG_LEVEL=INFO                 # Logging verbosity
```

### Model Configuration

Models can be configured per agent:
```python
agent = create_bank_support_agent(
    model_name="gpt-4o",
    temperature=0.3
)
```

## Development

### Adding New Agents

1. Define the agent in `src/agents.py`:
```python
def create_custom_agent(model_name: str = None) -> Agent[BankSupportContext]:
    model = OpenAIModel(model_name=model_name or "gpt-4o")
    return Agent(
        model=model,
        deps_type=BankSupportContext,
        system_prompt="Your custom prompt...",
        tools=selected_tools,
        name="Custom Agent"
    )
```

2. Register in the AGENTS dictionary:
```python
AGENTS["custom"] = create_custom_agent()
```

### Adding New Tools

1. Implement the tool in `src/tools.py`:
```python
async def custom_tool(
    ctx: RunContext[BankSupportContext],
    param: str
) -> str:
    """Tool description."""
    # Implementation
    return result
```

2. Add to BANK_SUPPORT_TOOLS list:
```python
BANK_SUPPORT_TOOLS.append(Tool.from_function(custom_tool))
```

### Creating New Scenarios

Create a JSON file in `src/scenarios/`:
```json
{
  "name": "Scenario Name",
  "description": "What this tests",
  "initial_context": {
    "authenticated": false
  },
  "conversation": [
    {
      "user": "User input",
      "expected": {
        "tools_called": ["tool_name"],
        "message_contains": ["expected text"]
      }
    }
  ]
}
```

## Testing

### Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions with mocked dependencies
- **Scenario Tests**: Full end-to-end conversation flows

### Test Fixtures

Key fixtures available in `conftest.py`:
- `test_context`: Pre-configured context with authentication
- `test_customer`: Sample customer data
- `test_accounts`: Sample account data
- `test_database`: In-memory test database
- `skip_if_no_api_key`: Skip tests requiring API access

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Ensure database is initialized
   - Check test credentials match seed data
   - Verify SSN format (4 digits)

2. **Tool Execution Errors**
   - Check database connectivity
   - Verify context has required fields
   - Ensure proper authentication before sensitive operations

3. **API Key Issues**
   - Confirm OPENAI_API_KEY is set in .env
   - Check API key has sufficient credits
   - Verify network connectivity

4. **Database Issues**
   - Run `python -m src.database_init` to reset database
   - Check DATABASE_PATH in .env points to valid location
   - Ensure write permissions for database directory

### Debug Mode

Enable verbose output for detailed execution logs:
```bash
uv run --env-file .env python -m src.runner src/scenarios/authentication_flow.json -v
```

## Performance Considerations

- Agents use temperature=0.3 for consistent responses
- Tools are async for optimal performance
- Database uses connection pooling for concurrent access
- Scenarios can run in parallel for faster testing

## Support

For questions or issues with this demo, please refer to the main project documentation or create an issue in the repository.