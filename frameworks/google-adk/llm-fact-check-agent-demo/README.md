# LLM Fact-Check Agent Demo

An automated fact-checking system built with Google Agent Development Kit (ADK) that verifies claims in LLM-generated text and corrects inaccuracies.

## Overview

This demo implements a multi-agent system that:
1. **Identifies and extracts claims** from Q&A pairs
2. **Verifies each claim** using Google Search and internal knowledge
3. **Assigns verdicts** (Accurate, Inaccurate, Disputed, Unsupported, Not Applicable)
4. **Automatically corrects** inaccurate information while preserving style

## Architecture

### Agent Structure

```
llm_fact_check_agent (SequentialAgent)
  critic_agent
    Model: gemini-2.5-flash
    Tools: google_search
    Role: Investigative journalist verifying claims
  reviser_agent
    Model: gemini-2.5-flash
    Tools: None (uses critic's findings)
    Role: Professional editor correcting inaccuracies
```

### Workflow

1. **Input**: Question-Answer pair to be fact-checked
2. **Critic Phase**:
   - Extracts all distinct claims from the answer
   - Searches for evidence using Google Search
   - Assigns verdict to each claim with justification
   - Provides overall assessment
3. **Reviser Phase**:
   - Reviews critic's findings
   - Minimally edits answer to correct inaccuracies
   - Maintains original style and structure
   - Balances disputed claims or softens unsupported ones
4. **Output**: Fact-checked and corrected answer

## Setup

### Prerequisites

- Python 3.10+
- Google Cloud Project or Gemini API key
- uv package manager

### Installation

1. Clone the repository:
```bash
cd llm-fact-check-agent-demo
```

2. Install dependencies using uv:
```bash
uv sync
```

### Environment Configuration

Create a `.env` file with the following variables:

```bash
GOOGLE_GENAI_USE_VERTEXAI=0
GOOGLE_API_KEY=your-api-key
```

## Usage

### Running Test Scenarios

```bash
# Execute a single scenario (saves a report JSON)
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/mixed_accuracy.json --verbose

# Run all scenarios (saves reports under reports/)
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner --verbose
```

## Testing

### Run Unit Tests

```bash
# Run all tests
unset VIRTUAL_ENV && uv run --env-file .env pytest

# Run specific test file
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/test_agents.py

# Run only unit tests (skip integration)
unset VIRTUAL_ENV && uv run --env-file .env pytest -m "not integration"

# Run integration tests (requires API key)
unset VIRTUAL_ENV && uv run --env-file .env pytest -m integration
```

### Test Scenarios

The demo includes several test scenarios in `src/scenarios/`:

1. **accurate_facts.json**: Tests with completely accurate information
2. **inaccurate_facts.json**: Tests with clear factual errors
3. **mixed_accuracy.json**: Tests with mix of accurate and inaccurate claims
4. **disputed_claims.json**: Tests with controversial or disputed information

### Scenario Structure

```json
{
  "name": "scenario_name",
  "description": "What this scenario tests",
  "conversation": [
    {
      "user": "Q: Question? A: Answer to fact-check.",
      "expected": {
        "tools_called": ["google_search"],
        "message_contains": ["keyword1", "keyword2"],
        "verdict": "Accurate|Inaccurate|Disputed"
      }
    }
  ]
}
```

## Project Structure

```
llm-fact-check-agent-demo/
  src/
    __init__.py
    agents.py          # Agent definitions and registry
    prompts.py         # Critic and Reviser prompts
    runner.py          # Scenario execution framework
    scenarios/         # Test scenarios
      accurate_facts.json
      inaccurate_facts.json
      mixed_accuracy.json
      disputed_claims.json
  tests/
    __init__.py
    conftest.py        # Pytest fixtures
    test_agents.py     # Comprehensive test suite
  pyproject.toml       # Project configuration
  README.md            # This file
  .env.example         # Environment variables template
```

## Verdict Types

The critic agent assigns one of these verdicts to each claim:

- **Accurate**: Information is correct and verified
- **Inaccurate**: Information contains errors or inconsistencies
- **Disputed**: Reliable sources offer conflicting information
- **Unsupported**: No reliable sources found to verify
- **Not Applicable**: Subjective opinion or fictional content

## Deployment

### Deploy to Vertex AI Agent Engine

```bash
# Install deployment dependencies
uv sync --group deployment

# Deploy agent
unset VIRTUAL_ENV && uv run --env-file .env python -c "
from google.cloud import aiplatform
# Deployment code here
"
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you're using `uv run` to execute commands
2. **API authentication**: Verify your Google Cloud credentials are configured
3. **Rate limiting**: The system uses Gemini Flash model for efficiency
4. **Search not working**: Ensure Google Search is enabled in your project

### Debug Mode

Run with verbose output to see detailed execution:

```python
runner = ScenarioRunner(verbose=True)
```

## Contributing

To add new test scenarios:

1. Create a JSON file in `src/scenarios/`
2. Define the Q&A pair and expected behavior
3. Run the scenario to validate

## License

Apache License 2.0

## Acknowledgments

Based on Google's [LLM Auditor example](https://github.com/google/adk-samples/tree/main/python/agents/llm-auditor) from the ADK samples repository.