# CrewAI Landing Page Generator Agent Demo

A sophisticated multi-agent system that automatically generates professional landing pages from simple ideas using CrewAI's orchestration framework.

## Overview

This demo showcases the power of CrewAI's multi-agent collaboration by implementing a landing page generator that transforms user ideas into fully functional, responsive HTML landing pages. The system employs specialized AI agents that work together to research, design, create content, and ensure quality.

## Features

- **Multi-Agent Collaboration**: Four specialized agents work together to generate landing pages
- **Intelligent Research**: Automatically expands ideas with market research and competitive analysis
- **Smart Template Selection**: Chooses the best template based on the concept
- **Content Generation**: Creates compelling, conversion-focused copy
- **Quality Assurance**: Reviews and validates the final output
- **Scenario Testing**: Comprehensive test framework with predefined scenarios
- **Responsive Design**: Generated pages work on all devices

## Architecture

### Agents

1. **Idea Analyst**: Researches and expands the initial concept
2. **Template Selector**: Evaluates and selects appropriate templates
3. **Content Creator**: Generates compelling landing page content
4. **Quality Assurance**: Reviews and ensures output quality

### Workflow

```
User Input → Idea Analysis → Template Selection → Content Creation → Quality Review → Final Output
```

## Installation

### Prerequisites

- Python 3.10 or 3.11
- OpenAI API key
- uv (recommended) or pip

### Setup

1. Create and activate virtual environment, then install dependencies using uv:
```bash
unset VIRTUAL_ENV && uv sync
```

This will automatically create a virtual environment, install all dependencies from `pyproject.toml`, and set up the project in editable mode.

## Usage

### Command Line Interface

#### Interactive Mode
```bash
unset VIRTUAL_ENV && uv run python -m src.runner
```

#### Direct Idea Input
```bash
unset VIRTUAL_ENV && uv run python -m src.runner --idea "Create a landing page for a fitness tracking app"
```

#### Run Test Scenarios
```bash
unset VIRTUAL_ENV && uv run python -m src.runner --scenario src/scenarios/simple_landing.json --verbose
```

### Python API

```python
from src.crew import LandingPageCrew

# Initialize the crew
crew = LandingPageCrew(model_name="gpt-4", verbose=True)

# Generate a landing page
result = crew.run("Create a landing page for a task management app")

if result["success"]:
    print(f"Landing page generated: {result['output_file']}")
```

### Running Tests

```bash
# Run all tests
unset VIRTUAL_ENV && uv run pytest

# Run with coverage
pytest --cov=src

# Run only unit tests
pytest -m unit

# Run integration tests (requires API key)
pytest -m integration
```

## Test Scenarios

The demo includes predefined test scenarios in `src/scenarios/`:

- **simple_landing.json**: Basic productivity app landing page
- **saas_landing.json**: Comprehensive SaaS product page
- **portfolio_landing.json**: Creative professional portfolio

### Running Scenarios

```bash
# Run a specific scenario
uv run python -m src.runner --scenario src/scenarios/saas_landing.json

# Generate report
uv run python -m src.runner --scenario src/scenarios/saas_landing.json --report results/output/report.json
```

## Project Structure

```
landing-page-generator-agent-demo/
├── src/
│   ├── agents.py           # Agent definitions
│   ├── tasks.py            # Task definitions
│   ├── crew.py             # Crew orchestration
│   ├── tools.py            # Custom tools for agents
│   ├── runner.py           # Scenario runner
│   └── scenarios/          # Test scenarios
│       ├── simple_landing.json
│       ├── saas_landing.json
│       └── portfolio_landing.json
├── tests/
│   ├── conftest.py         # Test fixtures
│   └── test_agents.py      # Comprehensive test suite
├── templates/
│   └── basic/              # Basic HTML template
│       └── index.html
├── pyproject.toml          # Project configuration
├── .env.example            # Environment variables template
└── README.md              # This file
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
MODEL_NAME=gpt-4              # Model to use (default: gpt-4)
TEMPERATURE=0.7               # Model temperature (default: 0.7)
CREW_VERBOSE=true             # Enable verbose output
MAX_ITERATIONS=10             # Max crew iterations
OUTPUT_DIR=./results/output   # Output directory
WORKDIR=./results/workdir     # Working directory
```

### Model Options

The system supports different OpenAI models:
- `gpt-4` (recommended for best results)
- `gpt-3.5-turbo` (faster and cheaper)

## Output

All generated files are stored in the `results/` directory:

Generated landing pages are saved to `results/output/` with timestamps:
- `landing_page_20240101_120000.html`

Intermediate results are stored in `results/workdir/`:
- `expanded_concept.json`
- `template_plan.json`
- `content.json`

## Development

### Adding New Agents

```python
from crewai import Agent

def custom_agent() -> Agent:
    return Agent(
        role="Custom Role",
        goal="Custom goal",
        backstory="Agent backstory",
        tools=[],
        allow_delegation=False
    )
```

### Creating Custom Tools

```python
from crewai_tools import tool

@tool
def CustomTool(param: str) -> str:
    """Custom tool description."""
    # Tool implementation
    return result
```

### Adding Test Scenarios

Create a new JSON file in `src/scenarios/`:

```json
{
  "name": "Scenario Name",
  "description": "Scenario description",
  "initial_idea": "Landing page idea",
  "conversation": [...],
  "expected_final_output": {...}
}
```

## Performance

- **Execution Time**: 2-5 minutes per landing page
- **API Costs**: Approximately $0.10-$0.50 per generation (GPT-4)
- **Success Rate**: >95% for well-defined ideas

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure OPENAI_API_KEY is set in .env
2. **Import Errors**: Install dependencies with `uv pip install -e .`
3. **Template Not Found**: Check templates directory exists
4. **Rate Limiting**: Reduce request frequency or upgrade API tier

### Debug Mode

Enable verbose output for debugging:
```bash
uv run python -m src.runner --verbose
```

## Limitations

- Requires OpenAI API access
- Generated content is AI-created and should be reviewed
- Template customization is limited to predefined options
- Performance depends on API response times

## Future Enhancements

- [ ] Add more template options
- [ ] Support for custom CSS frameworks
- [ ] Integration with design systems
- [ ] Multi-language support
- [ ] A/B testing variations
- [ ] SEO optimization features
- [ ] Performance optimization
- [ ] Export to various formats (React, Vue, etc.)

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [CrewAI](https://github.com/joaomdmoura/crewAI)
- Powered by OpenAI's GPT models
- Inspired by modern landing page best practices

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: robert@moyai.ai

## Citation

If you use this demo in your research or projects, please cite:

```bibtex
@software{crewai_landing_page_generator,
  title = {CrewAI Landing Page Generator Demo},
  author = {Robert Moyai},
  year = {2024},
  url = {https://github.com/your-repo/landing-page-generator-demo}
}
```