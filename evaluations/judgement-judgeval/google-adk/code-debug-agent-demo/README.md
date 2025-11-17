# Code Debug Agent Evaluation Suite

Comprehensive evaluation framework for the Google ADK Code Debug Agent using JudgmentLabs. This project provides automated testing and quality assessment of the agent's debugging capabilities across multiple programming languages and error types.

## Overview

This evaluation suite tests the Code Debug Agent's ability to:

- Analyze and understand error messages
- Search Stack Exchange for relevant solutions
- Provide actionable fixes and explanations
- Use appropriate tools for different error types
- Deliver complete and helpful responses

## Features

- **JudgmentLabs Integration**: Production-ready evaluation using the judgeval framework
- **Custom Scorers**: Specialized evaluators for debugging scenarios
  - Solution Quality Scorer: Evaluates solution relevance and actionability
  - Tool Usage Scorer: Assesses appropriate tool selection
  - Response Completeness Scorer: Measures response thoroughness
- **Multi-Language Support**: Test scenarios for Python, JavaScript, TypeScript, and more
- **Rich Reporting**: Detailed evaluation results with visualized metrics
- **Observability Ready**: Compatible with Langfuse and LangSmith tracing
- **CI/CD Integration**: Automated testing with pass/fail assertions

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Google API key for Gemini models
- JudgmentLabs API credentials

### Setup

1. Navigate to the evaluation directory:

```bash
cd evaluations/judgement-judgeval/google-adk/code-debug-agent-demo
```

2. Install dependencies using uv:

```bash
unset VIRTUAL_ENV && uv sync
```

3. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Running Evaluations

The evaluation suite uses Python's standard console entry point system via `pyproject.toml`. The `run-eval` command is automatically available after running `uv sync`, providing a clean CLI interface while properly handling module namespace conflicts.

> **Note on uv Scripts**: While uv's inline script dependencies (PEP 723) are great for standalone scripts, they don't work well when you need to import from multiple projects that both use `src/` as their package name. Python's module system would resolve imports incorrectly, causing `ModuleNotFoundError`. Our solution uses standard Python packaging with console entry points and careful `sys.modules` management.

#### Basic Evaluation

Run evaluation on a scenario file using the console entry point:

```bash
unset VIRTUAL_ENV && uv run run-eval scenarios/python_errors.json
```

Or use the module directly:

```bash
unset VIRTUAL_ENV && uv run python -m src.evaluator scenarios/python_errors.json
```

#### Run All Scenarios in `scenarios/`

You can now execute every JSON file under `scenarios/` with a single flag—no shell loop required:

```bash
unset VIRTUAL_ENV && uv run run-eval --all-scenarios
```

This scans the local `scenarios/` folder, sequentially evaluates each file (currently `python_errors.json`, `javascript_errors.json`, and `mixed_errors.json`), and stores separate reports in `eval_results/`. Customize the run by combining flags:

```bash
unset VIRTUAL_ENV && uv run run-eval --all-scenarios \
  --agent quick_debug_agent \
  --project my-custom-project
```

To point at a different directory of scenarios, include `--scenarios-dir /absolute/path/to/scenarios`. When using `--run-name foo` alongside `--all-scenarios`, result files will be suffixed automatically (e.g., `foo_python_errors.json`).

Multi-turn conversations defined in those files are replayed faithfully, and any
`expected_tools` / `expected_keywords` declared on individual turns are merged
automatically for scoring.

#### Specify Agent

Evaluate a specific agent variant:

```bash
uv run run-eval scenarios/python_errors.json --agent quick_debug_agent
```

#### Custom Project Name

Use a custom JudgmentLabs project:

```bash
uv run run-eval scenarios/python_errors.json --project my-custom-project
```

#### CI/CD Mode

Run with assertions (fails on threshold violations):

```bash
uv run run-eval scenarios/python_errors.json --assert-test
```

### Available Scenarios

The suite includes pre-built scenario files:

- `scenarios/python_errors.json` - Python-specific errors (ImportError, TypeError, etc.)
- `scenarios/javascript_errors.json` - JavaScript and React errors
- `scenarios/mixed_errors.json` - Cross-language and framework errors
- Agent-provided samples under `../../../../frameworks/google-adk/code-debug-agent-demo/src/scenarios/*.json`

### Alternative: Using the Module Directly

You can also run the evaluator as a Python module (requires `uv sync` first):

```bash
# Install dependencies first
uv sync

# Run evaluator module
uv run python -m src.evaluator scenarios/python_errors.json
```

Or use the convenience bash script:

```bash
uv run run-eval scenarios/python_errors.json
```

## Evaluation Metrics

### Solution Quality Scorer

Evaluates the quality of debugging solutions (threshold: 0.7):

- **Expected Keywords** (30%): Contains relevant solution terms
- **Actionable Fixes** (30%): Provides concrete steps to resolve the error
- **References** (20%): Includes Stack Overflow or documentation links
- **Root Cause Explanation** (20%): Explains why the error occurred

### Tool Usage Scorer

Assesses appropriate tool selection (threshold: 0.8):

- **Expected Tools Called** (70%): Agent calls the right tools for the error type
- **No Unnecessary Tools** (30%): Avoids calling irrelevant tools

### Response Completeness Scorer

Measures response thoroughness (threshold: 0.7):

- **Adequate Length** (20%): Response is sufficiently detailed
- **Multiple Solutions** (30%): Provides alternative approaches
- **Code Examples** (30%): Includes code snippets or commands
- **Additional Context** (20%): Offers helpful tips and warnings

## Project Structure

```
evaluation/
├── src/
│   ├── __init__.py
│   ├── data_models.py          # Pydantic models for evaluation
│   ├── agent_wrapper.py        # Agent execution wrapper
│   └── evaluator.py            # Main evaluation runner
├── scorers/
│   ├── __init__.py
│   ├── solution_quality_scorer.py
│   ├── tool_usage_scorer.py
│   └── response_completeness_scorer.py
├── scenarios/
│   ├── python_errors.json
│   ├── javascript_errors.json
│   └── mixed_errors.json
├── eval_results/               # Generated evaluation reports
├── tests/
│   └── test_evaluator.py
├── pyproject.toml
├── README.md
└── .env.example
```

## Creating Custom Scenarios

Create a JSON file with your test cases:

```json
{
  "scenarios": [
    {
      "name": "Your Scenario Name",
      "description": "Description of what you're testing",
      "error_message": "The actual error message",
      "programming_language": "python",
      "framework": "django",
      "expected_tools": ["search_stack_exchange_for_error"],
      "expected_keywords": ["solution", "fix", "install"]
    }
  ]
}
```

### Scenario Fields

- `name` (required): Descriptive name for the scenario
- `description` (optional): What this scenario tests
- `error_message` (required): The error to debug
- `programming_language` (optional): Language context (python, javascript, etc.)
- `framework` (optional): Framework context (react, django, etc.)
- `expected_tools` (optional): Tools the agent should call
- `expected_keywords` (optional): Keywords expected in good solutions

## Custom Scorers

Create custom scorers by extending `ExampleScorer`:

```python
from judgeval.scorers.example_scorer import ExampleScorer
from src.data_models import DebugAgentExample

class MyCustomScorer(ExampleScorer):
    name: str = "My Custom Scorer"
    threshold: float = 0.8

    async def a_score_example(self, example: DebugAgentExample) -> float:
        # Your scoring logic here
        score = 0.0

        if "specific_keyword" in example.agent_response.lower():
            score += 0.5

        self.reason = "Explanation of the score"
        return score
```

Add your scorer to the evaluator in `src/evaluator.py`:

```python
from scorers.my_custom_scorer import MyCustomScorer

scorers = [
    SolutionQualityScorer(threshold=0.7),
    ToolUsageScorer(threshold=0.8),
    ResponseCompletenessScorer(threshold=0.7),
    MyCustomScorer(threshold=0.8),  # Add here
]
```

## Integration with Observability

### Langfuse Integration

The evaluation runner can stream Langfuse traces without any extra wiring:

1. Export your Langfuse credentials (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and optionally `LANGFUSE_HOST`).
2. Run the evaluator with the Langfuse flag:

```bash
unset VIRTUAL_ENV && uv run python -m src.evaluator scenarios/python_errors.json --use-langfuse
```

This code path uses the traced runner from `/Users/roberthommes/moyai/projects/multi-framework-agent-evals/observability/langfuse/google-adk/code-debug-agent-demo`, so each scenario execution appears in the Langfuse dashboard with the scenario metadata attached.

### LangSmith Integration

Similarly, you can route executions through the LangSmith traced runner:

```bash
unset VIRTUAL_ENV && uv run python -m src.evaluator scenarios/python_errors.json --use-langsmith
```

Set `LANGSMITH_API_KEY` (and optionally `LANGSMITH_PROJECT`) before running. Only one observability backend can be enabled at a time.

## Results and Reports

### Console Output

Evaluation results are displayed in a formatted table showing:
- Overall pass/fail status
- Individual scorer results
- Detailed metrics per scenario

### JSON Reports

Detailed results are saved to `eval_results/` in JSON format:

```json
{
  "eval_run_name": "python_errors",
  "timestamp": "2025-01-17T10:30:00",
  "agent_name": "debug_agent",
  "summary": {
    "total": 5,
    "passed": 4,
    "failed": 1
  },
  "results": [
    {
      "scenario_index": 0,
      "error_message": "ImportError: No module named 'pandas'",
      "success": true,
      "scorers": [...]
    }
  ]
}
```

### JudgmentLabs Dashboard

View detailed analytics and trends at:
- https://app.judgmentlabs.ai

## Testing

Run the test suite:

```bash
unset VIRTUAL_ENV && uv run pytest
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Agent Evaluation

on: [push, pull_request]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: cd evaluation && uv sync

      - name: Run evaluations
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
          JUDGMENT_API_KEY: ${{ secrets.JUDGMENT_API_KEY }}
          JUDGMENT_ORG_ID: ${{ secrets.JUDGMENT_ORG_ID }}
        run: |
          cd evaluation
          uv run python -m src.evaluator scenarios/python_errors.json --assert-test
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the evaluation directory when running commands
2. **API Rate Limits**: Add a Stack Exchange API key to increase rate limits
3. **Agent Not Found**: Verify the agent name matches those in the main project
4. **Evaluation Timeout**: Some scenarios may take time; consider running subsets

### Debug Mode

Enable verbose logging:

```bash
export DEBUG=1
unset VIRTUAL_ENV && uv run python -m src.evaluator scenarios/python_errors.json
```

## Resources

- [Google ADK Documentation](https://github.com/google/adk)
- [JudgmentLabs Documentation](https://docs.judgmentlabs.ai/documentation)
- [JudgmentLabs judgeval README](https://deepwiki.com/JudgmentLabs/judgeval?tab=readme-ov-file)
- [Main Agent Implementation](/Users/roberthommes/moyai/projects/multi-framework-agent-evals/frameworks/google-adk/code-debug-agent-demo)
- [Langfuse Tracing Implementation](/Users/roberthommes/moyai/projects/multi-framework-agent-evals/observability/langfuse/google-adk/code-debug-agent-demo)
- [LangSmith Tracing Implementation](/Users/roberthommes/moyai/projects/multi-framework-agent-evals/observability/langsmith/google-adk/code-debug-agent-demo)
