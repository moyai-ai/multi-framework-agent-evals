# Lead Qualification Agent Demo - Pydantic AI

A sophisticated lead qualification system built with [Pydantic AI](https://ai.pydantic.dev/) that automatically researches and qualifies sales leads using web search powered by [Linkup.so](https://www.linkup.so/).

## Overview

This demo showcases how to build an intelligent lead qualification agent that:

- **Researches leads automatically** using web search to gather information about individuals and companies
- **Analyzes qualification criteria** based on company size, technology stack, and decision-making authority
- **Provides actionable insights** including qualification scores, confidence levels, and talking points
- **Supports batch processing** for qualifying multiple leads in parallel
- **Generates priority lists** for sales outreach optimization

Inspired by the [Slack Lead Qualifier example](https://ai.pydantic.dev/examples/slack-lead-qualifier/), this implementation demonstrates enterprise-grade lead qualification for B2B software sales.

## Key Features

### Intelligent Lead Analysis
- **Person Analysis**: Evaluates professional background, seniority, technical expertise, and decision-making authority
- **Company Analysis**: Assesses company size, industry, tech stack, and engineering capabilities
- **Qualification Scoring**: Six-tier scoring system from VERY_HIGH to UNQUALIFIED with confidence ratings

### Advanced Capabilities
- **Web Research Integration**: Uses Linkup.so for real-time web searches about leads and companies
- **Parallel Processing**: Qualify multiple leads simultaneously for efficiency
- **Priority Ranking**: Automatically prioritizes leads for sales outreach
- **Actionable Recommendations**: Provides specific talking points and next actions

### Structured Output
- Uses Pydantic models for type-safe, validated data structures
- Native integration with OpenAI's structured output capabilities
- Comprehensive analysis reports with reasoning and confidence scores

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key
- Linkup.so API key (for web search capabilities)

### Setup

1. Install dependencies using uv:
```bash
unset VIRTUAL_ENV && uv sync
```

Get your API keys:
- OpenAI: https://platform.openai.com/api-keys
- Linkup.so: https://www.linkup.so/

## Usage

### Quick Start

Run the main demo application:

```bash
unset VIRTUAL_ENV && uv run python src/main.py
```

This provides an interactive menu with options to:
- Run a quick demo with pre-configured leads
- Enter your own lead information for qualification
- Run the full demo suite with multiple scenarios
- Process multiple leads in batch mode

### Programmatic Usage

```python
import asyncio
from src.agent.lead_qualifier import LeadQualificationAgent
from src.agent.models import Lead

async def qualify_lead_example():
    # Initialize the agent
    agent = LeadQualificationAgent(model="gpt-4o-mini")

    # Create a lead
    lead = Lead(
        name="Sarah Chen",
        email="s.chen@techcorp.com",
        company="TechCorp Global",
        title="VP of Engineering",
        source="conference"
    )

    # Qualify the lead
    analysis = await agent.qualify_lead(lead)

    # Display results
    print(f"Score: {analysis.score.value}")
    print(f"Confidence: {analysis.confidence:.1%}")
    print(f"Summary: {analysis.summary}")
    print(f"Recommended Action: {analysis.recommended_action}")

    # Get talking points
    for point in analysis.talking_points:
        print(f"- {point}")

# Run the example
asyncio.run(qualify_lead_example())
```

### Batch Processing

```python
async def batch_qualification():
    agent = LeadQualificationAgent()

    leads = [
        Lead(name="Lead 1", email="lead1@company.com", company="Company A"),
        Lead(name="Lead 2", email="lead2@company.com", company="Company B"),
        Lead(name="Lead 3", email="lead3@company.com", company="Company C"),
    ]

    # Qualify all leads in parallel
    analyses = await agent.qualify_batch(leads, parallel=True)

    # Get high-value leads
    high_value = agent.get_high_value_leads(
        analyses,
        min_score=QualificationScore.HIGH,
        min_confidence=0.7
    )

    # Generate priority list
    priority_list = agent.generate_outreach_priority_list(analyses)
```

## Demo Scenarios

The demo includes several pre-built scenarios to showcase different aspects:

### 1. Single Lead Qualification
Demonstrates detailed analysis of an individual lead with full research and qualification.

### 2. Batch Processing
Shows parallel processing of multiple leads with summary results.

### 3. Priority Ranking
Generates a prioritized list of leads for sales outreach based on qualification scores.

### 4. Scenario Comparison
Compares qualification results across different lead types:
- High-priority enterprise leads
- Technical influencers
- Unqualified leads

## Running the Scenarios

### Method 1: Command Line (Quick)

Run specific scenarios directly from the command line:

```bash
# Show available scenarios
uv run python src/run_scenario.py

# Run single lead qualification
uv run python src/run_scenario.py single

# Run batch processing demo
uv run python src/run_scenario.py batch

# Run priority ranking demo
uv run python src/run_scenario.py priority

# Run scenario comparison
uv run python src/run_scenario.py comparison

# Run all demos sequentially
uv run python src/run_scenario.py all
```

**Testing without API keys:**
```bash
# Test imports and basic functionality
uv run python src/test_scenario.py

# Test demo displays with mock data (no API calls)
uv run python src/test_demo_structure.py
```

### Method 2: Interactive Menu

For a guided experience with menu options:

```bash
uv run python src/main.py
```

This will present you with options:
1. **Quick Demo** - Run a single pre-configured lead qualification
2. **Interactive Mode** - Enter your own lead information
3. **Full Demo Suite** - Run all scenarios sequentially
4. **Batch Processing Demo** - Process 5 sample leads in parallel

### Method 3: Programmatic Execution

You can also run specific scenarios programmatically:

```python
# Run a specific scenario directly
import asyncio
from src.scenarios.demo_runner import DemoRunner
from src.scenarios.sample_leads import get_sample_leads

async def run_scenarios():
    runner = DemoRunner(model="gpt-4o-mini")

    # Run single lead demo
    lead = get_sample_leads()[0]
    await runner.run_single_lead_demo(lead)

    # Run batch processing (5 leads in parallel)
    await runner.run_batch_demo()

    # Run priority ranking demo
    await runner.run_priority_ranking_demo()

    # Run scenario comparison
    await runner.run_scenario_comparison()

    # Or run all demos
    await runner.run_all_demos()

# Execute
asyncio.run(run_scenarios())
```

### Using Sample Data

The demo includes pre-configured sample leads in different categories:

```python
from src.scenarios.sample_leads import (
    get_sample_leads,           # All 8 sample leads
    get_high_priority_leads,     # Enterprise decision makers
    get_technical_leads,         # Technical influencers
    get_unqualified_leads        # Leads that won't qualify
)

# Example: Qualify only high-priority leads
import asyncio
from src.agent.lead_qualifier import LeadQualificationAgent

async def qualify_high_priority():
    agent = LeadQualificationAgent()
    leads = get_high_priority_leads()

    analyses = await agent.qualify_batch(leads, parallel=True)

    for analysis in analyses:
        print(f"{analysis.person_analysis.name}: {analysis.score.value}")
        print(f"  Confidence: {analysis.confidence:.1%}")
        print(f"  Action: {analysis.recommended_action}\n")

asyncio.run(qualify_high_priority())
```

### What Each Scenario Demonstrates

1. **Single Lead Demo** (`single`):
   - Shows detailed qualification process
   - Displays person and company analysis
   - Provides talking points and recommendations
   - Shows confidence scores and reasoning

   Example output:
   ```
   Score: VERY_HIGH
   Confidence: 92%
   Summary: Enterprise VP of Engineering at a Python-heavy company...
   Recommended Action: immediate_outreach
   ```

2. **Batch Processing Demo** (`batch`):
   - Processes multiple leads simultaneously
   - Generates summary table with scores
   - Identifies high-value leads automatically
   - Shows performance of parallel processing

   Example output:
   ```
   ┌─────────────────┬──────────┬─────────┬────────────┬───────────────┐
   │ Name            │ Company  │ Score   │ Confidence │ Action        │
   ├─────────────────┼──────────┼─────────┼────────────┼───────────────┤
   │ Sarah Chen      │ TechCorp │ HIGH    │ 85%        │ immediate     │
   │ Michael Rodriguez│ DataFlow │ MEDIUM  │ 72%        │ nurture       │
   └─────────────────┴──────────┴─────────┴────────────┴───────────────┘
   ```

3. **Priority Ranking Demo** (`priority`):
   - Qualifies 6 leads and ranks them by value
   - Creates prioritized outreach list
   - Shows top priority lead details
   - Demonstrates scoring algorithm

   Example output:
   ```
   Sales Outreach Priority List:
   1. Patricia Anderson (CTO) - FinanceCorp - VERY_HIGH (95%)
   2. Sarah Chen (VP Eng) - TechCorp - HIGH (85%)
   3. Emily Watson (CTO) - AIStart - HIGH (80%)
   ```

4. **Scenario Comparison Demo** (`comparison`):
   - Compares different lead categories side-by-side
   - Shows average confidence per category
   - Displays score distribution
   - Validates qualification logic

   Example output:
   ```
   High Priority Leads:
     • Average Confidence: 88.3%
     • Score Distribution:
       - very_high: 2
       - high: 1

   Technical Leads:
     • Average Confidence: 75.0%
     • Score Distribution:
       - high: 1
       - medium: 2
   ```

## Running Tests

The project includes comprehensive unit tests:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_lead_qualifier.py

# Run tests with verbose output
uv run pytest -v
```

Test coverage includes:
- Data model validation
- Agent initialization and configuration
- Lead qualification logic
- Batch processing
- Web search integration
- Priority ranking algorithms

## Project Structure

```
lead-qual-agent-demo/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main application entry point
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── lead_qualifier.py   # Core agent implementation
│   │   └── models.py            # Pydantic data models
│   ├── tools/
│   │   ├── __init__.py
│   │   └── linkup_search.py    # Linkup.so integration
│   └── scenarios/
│       ├── __init__.py
│       ├── demo_runner.py      # Demo execution logic
│       └── sample_leads.py     # Sample data for demos
├── tests/
│   ├── __init__.py
│   ├── test_models.py          # Model validation tests
│   ├── test_lead_qualifier.py  # Agent logic tests
│   └── test_linkup_search.py   # Search tool tests
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## Configuration

### Agent Configuration

The agent can be configured with different models and parameters:

```python
agent = LeadQualificationAgent(
    model="gpt-4o-mini",  # or "gpt-4", "gpt-3.5-turbo"
    api_key="your-api-key",  # Optional, uses env var by default
    linkup_api_key="your-linkup-key"  # Optional, uses env var by default
)
```

### Qualification Criteria

The agent uses the following qualification tiers:

- **VERY_HIGH**: Enterprise companies with large engineering teams using Python, lead is a decision-maker
- **HIGH**: Mid-market companies with engineering teams using Python, lead has purchasing authority
- **MEDIUM**: Growing companies with technical needs, lead is an influencer or technical lead
- **LOW**: Small companies with limited technical resources, lead has no clear authority
- **VERY_LOW**: Companies unlikely to need developer tools, lead not in relevant role
- **UNQUALIFIED**: No fit with product, wrong industry, or insufficient information

## Advanced Features

### Custom Context

Provide additional context for more accurate qualification:

```python
context = {
    "product_focus": "ML monitoring tools",
    "ideal_company_size": "enterprise",
    "target_industries": ["fintech", "healthcare", "saas"]
}

analysis = await agent.qualify_lead(lead, context=context)
```

### Filtering High-Value Leads

```python
# Get only very high and high scored leads with 80%+ confidence
high_value_leads = agent.get_high_value_leads(
    analyses,
    min_score=QualificationScore.HIGH,
    min_confidence=0.8
)
```

### Custom Talking Points

The agent generates specific talking points based on the lead's profile:
- Technical capabilities and stack alignment
- Business pain points and solutions
- Industry-specific value propositions
- Competitive advantages

## Troubleshooting

### Common Issues

1. **Missing API Keys**
   - Ensure both OPENAI_API_KEY and LINKUP_API_KEY are set
   - Check .env file is in the correct directory

2. **Import Errors**
   - Run `unset VIRTUAL_ENV && uv sync` to install dependencies
   - Ensure Python 3.11+ is installed

3. **Rate Limiting**
   - The agent includes retry logic for API calls
   - Consider using batch processing with delays for large datasets

4. **Timeout Errors**
   - Increase timeout in LinkupSearchTool initialization
   - Default is 30 seconds, can be increased for complex searches

## Contributing

Contributions are welcome! Please ensure:
- All tests pass (`uv run pytest`)
- Code follows the existing style
- New features include appropriate tests
- Documentation is updated accordingly

## License

This demo is provided as an example implementation and is subject to the terms of the parent repository.

## Acknowledgments

- [Pydantic AI](https://ai.pydantic.dev/) for the agent framework
- [Linkup.so](https://www.linkup.so/) for web search capabilities
- Inspired by the [Slack Lead Qualifier example](https://ai.pydantic.dev/examples/slack-lead-qualifier/)

## Support

For issues or questions about this demo:
- Review the test files for usage examples
- Check the inline documentation in the source code
- Refer to the Pydantic AI documentation: https://ai.pydantic.dev/

---

**Note**: This is a demonstration project showcasing Pydantic AI capabilities for lead qualification. The sample leads and scenarios are fictional and for demonstration purposes only.