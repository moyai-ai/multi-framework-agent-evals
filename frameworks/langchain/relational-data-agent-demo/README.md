# Relational Data Agent

A sophisticated multi-agent system for querying and analyzing relational databases using LangChain. This system showcases how specialized AI agents can collaborate to understand database schemas, generate SQL queries, analyze results, and produce comprehensive reports.

## Features

- **Multi-Agent Architecture**: Specialized agents for different aspects of database interaction
- **Natural Language to SQL**: Convert plain English requests into optimized SQL queries
- **Intelligent Schema Analysis**: Automatically understand table relationships and suggest optimal joins
- **Data Analysis & Insights**: Identify patterns, trends, and anomalies in query results
- **Safety Checks**: Prevent dangerous operations and validate queries before execution
- **Comprehensive Testing**: Scenario-based testing with validation

## Agent Architecture

The system uses an orchestrator pattern with specialized sub-agents:

### 1. **Orchestrator Agent**
- Coordinates all sub-agents
- Manages conversation context
- Routes requests to appropriate specialists

### 2. **Schema Analyst Agent**
- Analyzes database structure
- Identifies required tables and relationships
- Suggests optimal join paths

### 3. **Query Builder Agent**
- Generates SQL queries from natural language
- Optimizes queries for performance
- Validates query safety

### 4. **Data Analyst Agent**
- Analyzes query results
- Identifies patterns and insights
- Suggests follow-up analyses

### 5. **Report Writer Agent**
- Formats results into professional reports
- Creates visualizations
- Highlights key findings

## Installation

### Prerequisites

- Python 3.13 or higher
- OpenAI API key

### Setup

1. Install dependencies using uv:
```bash
uv sync
```

2. Add your OpenAI API key to `.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Listing Available Agents

To see which agents are implemented in the system:

```bash
# List all agents with their details
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner list-agents

# Shorter alias
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner agents
```

This command displays:
- Agent name and type
- Model being used
- Tools available to each agent

### Running Test Scenarios

The system's capabilities are showcased through comprehensive test scenarios that demonstrate various query patterns and analysis capabilities:

```bash
# Run all scenarios
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner test

# Run specific category
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner test simple_query
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner test aggregation
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner test complex

# Run interactive demo
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner demo
```

### Example Queries

The test scenarios include various query types:

1. **Simple Queries**:
   - "Show me all customers from New York"
   - "List products in the Electronics category"

2. **Join Queries**:
   - "Show me all orders with customer names"
   - "Display order details including product information"

3. **Aggregations**:
   - "What are the total sales by month?"
   - "Show me the top 5 customers by purchase amount"

4. **Complex Analysis**:
   - "Analyze customer purchasing patterns"
   - "Which products have low stock but high demand?"

## Project Structure

```
relational-data-agent/
├── pyproject.toml           # Project dependencies and configuration
├── .env.example             # Environment variables template
├── README.md               # This file
├── src/
│   ├── __init__.py
│   ├── agents.py           # Agent implementations
│   ├── tools.py            # SQL operation tools
│   ├── database.py         # Database models and setup
│   ├── context.py          # Context management
│   ├── prompts.py          # Agent system prompts
│   ├── runner.py           # Main execution and test runner
│   ├── data/
│   │   └── seed_data.sql   # Sample database data
│   └── scenarios/
│       └── test_cases.json # Test scenario definitions
└── tests/
    ├── conftest.py         # Test fixtures
    ├── test_agents.py      # Agent tests
    └── test_tools.py       # Tool tests
```

## Database Schema

The system uses a sample e-commerce database with the following tables:

- **customers**: Customer information
- **products**: Product catalog
- **orders**: Order records
- **order_items**: Individual items in orders
- **inventory_logs**: Stock change tracking

## Tools

The system includes specialized tools for database operations:

1. **schema_inspector_tool**: Examines database structure
2. **sql_executor_tool**: Safely executes SQL queries
3. **data_validator_tool**: Validates query parameters
4. **aggregation_tool**: Performs complex aggregations
5. **visualization_tool**: Creates text-based charts

## Testing

Run the test suite:

```bash
# Run all tests
unset VIRTUAL_ENV && uv run pytest

# Run specific test file
unset VIRTUAL_ENV && uv run pytest tests/test_agents.py

# Run tests with markers
unset VIRTUAL_ENV && uv run pytest -m unit
```

## Scenario Testing

The system includes comprehensive scenario-based testing:

- **Simple Queries**: Basic SELECT statements
- **Join Operations**: Multi-table queries
- **Aggregations**: GROUP BY, COUNT, SUM operations
- **Complex Analysis**: Multi-step analytical queries
- **Error Handling**: Invalid queries and edge cases
- **Safety Checks**: Preventing dangerous operations

View test scenarios in `src/scenarios/test_cases.json`.

## Development

### Adding New Agents

1. Create agent class in `src/agents.py`
2. Add system prompt in `src/prompts.py`
3. Register in `AGENTS` dictionary
4. Add tests in `tests/test_agents.py`

### Adding New Tools

1. Implement tool function in `src/tools.py`
2. Use `@tool` decorator from LangChain
3. Add to `get_all_tools()` function
4. Add tests in `tests/test_tools.py`

### Adding Test Scenarios

1. Edit `src/scenarios/test_cases.json`
2. Define scenario with validation criteria
3. Run with `python src/runner.py test`

## Best Practices

1. **Query Safety**: All queries are validated before execution
2. **Context Management**: Maintain conversation context across queries
3. **Error Handling**: Graceful handling of failures
4. **Testing**: Comprehensive unit and integration tests
5. **Documentation**: Clear documentation for all components

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**:
   - Ensure `.env` file exists with valid API key
   - Check environment variable is loaded

2. **Database Connection Error**:
   - Verify SQLite is installed
   - Check file permissions for database directory

3. **Import Errors**:
   - Install all dependencies: `uv sync`
   - Ensure Python 3.9+ is used

## Contributing

1. Follow existing code structure and patterns
2. Add tests for new features
3. Update documentation
4. Run tests before submitting

## License

This is a demonstration project for educational purposes.

## Acknowledgments

- Built with [LangChain](https://langchain.com/)
- Uses OpenAI GPT models for agent intelligence
- Inspired by LangChain benchmarks for relational data