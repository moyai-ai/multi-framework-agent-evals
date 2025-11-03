# Meta Quest Knowledge Agent Demo - CrewAI

A PDF-based knowledge agent demo built with CrewAI that answers questions about Meta Quest using official documentation. This demo showcases how to build intelligent agents that can search, retrieve, and synthesize information from PDF documents to provide accurate answers.

## Features

- **PDF Knowledge Base**: Processes Meta Quest documentation stored as PDFs
- **Vector Search**: Uses FAISS for efficient semantic search across documents
- **Multiple Agents**: Knowledge Expert and Technical Support specialists
- **Multi-Turn Conversations**: Maintains context across multiple questions
- **Scenario-Based Testing**: JSON scenarios for validating agent responses
- **CLI Interface**: Interactive mode and batch scenario execution
- **Comprehensive Tests**: Unit and integration tests with pytest

## Architecture

### Agents

1. **Knowledge Expert Agent**
   - Role: Meta Quest Knowledge Expert
   - Specialization: Comprehensive Q&A about Meta Quest
   - Tools: Document search, topic research, overview retrieval

2. **Technical Support Agent**
   - Role: Technical Support Specialist
   - Specialization: Troubleshooting and technical guidance
   - Tools: Same as Knowledge Expert, optimized for technical queries

### Tools

- `search_meta_quest_docs`: Search documentation for specific queries
- `get_meta_quest_overview`: Retrieve general Meta Quest overview
- `search_specific_topic`: Deep dive into specific topics

### Workflow

```
User Question → Agent Selection → Task Creation → Tool Execution →
PDF Vector Search → Context Retrieval → LLM Processing → Answer Generation
```

## Prerequisites

- **Python**: 3.10, 3.11, or 3.12
- **UV Package Manager**: Install via `pip install uv`
- **OpenAI API Key**: Required for LLM access

## Installation

1. **Clone or navigate to this directory**:
   ```bash
   cd frameworks/crewai/meta-quest-knowledge-agent-demo
   ```

2. **Install dependencies using UV**:
   ```bash
   unset VIRTUAL_ENV && uv sync --dev
   ```

3. **Add PDF documentation** (optional):
   ```bash
   # Place Meta Quest PDF files in the knowledge/ directory
   # A sample text-based guide is already included
   ```

## Configuration

### Environment Variables (.env)

```bash
# OpenAI Configuration (required)
OPENAI_API_KEY=your-openai-api-key-here

# Model Settings
MODEL_NAME=gpt-4o                # LLM model to use
TEMPERATURE=0.7                  # Response creativity (0.0-1.0)

# CrewAI Settings
CREW_VERBOSE=true                # Enable detailed logging
MAX_ITERATIONS=10                # Max agent iterations
MAX_RETRY_ATTEMPTS=3             # Retry attempts on failure

# Directory Configuration
KNOWLEDGE_DIR=./knowledge        # PDF knowledge base location
OUTPUT_DIR=./results/output      # Results output directory
WORKDIR=./results/workdir        # Working directory for intermediate files

# Logging
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR

# Feature Flags
ENABLE_SEARCH=false              # Enable web search (if needed)
ENABLE_WEB_SCRAPING=false        # Enable web scraping (if needed)
```

## Usage

### List Available Agents

```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner --list-agents
```

### Interactive Mode

Ask questions interactively:

```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner --interactive
```

Example session:
```
You: What is Meta Quest?
Agent: Meta Quest is a line of virtual reality (VR) headsets...

You: How do I set it up?
Agent: To set up your Meta Quest headset: 1. Charge your headset...
```

### Run Scenario Files

Execute a specific scenario:

```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/basic_qa_scenario.json
```

Run all scenarios in the scenarios directory:

```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner
```

### Verbose Mode

Enable detailed output:

```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner --verbose
```

### Using the Python API

```python
from src.crew import create_crew

# Create crew instance
crew = create_crew()

# Answer a single question
response = crew.answer_question("What is Meta Quest?")
print(response)

# Answer multiple questions
questions = [
    "What are the key features?",
    "How do I charge the battery?"
]
response = crew.answer_multiple_questions(questions)
print(response)

# Research a topic
response = crew.research_topic("hand tracking")
print(response)
```

## Testing

### Run All Tests

```bash
unset VIRTUAL_ENV && uv run --env-file .env pytest
```

### Run Unit Tests Only (no API key required)

```bash
unset VIRTUAL_ENV && uv run --env-file .env pytest -m unit
```

### Run Integration Tests (requires API key)

```bash
unset VIRTUAL_ENV && uv run --env-file .env pytest -m integration
```

### Run Specific Test File

```bash
unset VIRTUAL_ENV && uv run --env-file .env pytest tests/test_agents.py -v
```

## Project Structure

```
meta-quest-knowledge-agent-demo/
├── .env                        # Environment configuration
├── .gitignore                  # Git ignore rules
├── pyproject.toml              # Project dependencies and config
├── README.md                   # This file
├── uv.lock                     # Locked dependencies
│
├── knowledge/                  # PDF knowledge base
│   ├── README.md               # Knowledge base documentation
│   └── meta_quest_guide.txt    # Sample Meta Quest guide
│
├── src/                        # Source code
│   ├── __init__.py
│   ├── agents.py               # Agent definitions
│   ├── crew.py                 # Crew orchestration
│   ├── runner.py               # Main CLI runner
│   ├── tasks.py                # Task definitions
│   ├── tools.py                # PDF search and retrieval tools
│   └── scenarios/              # Test scenarios
│       ├── basic_qa_scenario.json
│       ├── multi_turn_scenario.json
│       └── setup_scenario.json
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   └── test_agents.py          # Agent tests
│
└── results/                    # Output directory
    ├── output/                 # Scenario results
    └── workdir/                # Intermediate files
```

## Scenarios

### Basic Q&A Scenario

Tests fundamental question-answering capabilities:
- What is Meta Quest?
- Key features
- Battery and charging

### Multi-Turn Conversation Scenario

Tests context retention across multiple questions:
- Controller information
- Hand tracking details
- Follow-up questions
- Game recommendations

### Setup Scenario

Tests setup and configuration guidance:
- First-time setup
- Phone requirements
- WiFi connection

## Available Agents

### Knowledge Expert
- **Name**: `knowledge_expert`
- **Role**: Meta Quest Knowledge Expert
- **Best For**: General questions, feature explanations, comprehensive answers
- **Tools**: All document search tools

### Technical Support
- **Name**: `technical_support`
- **Role**: Technical Support Specialist
- **Best For**: Troubleshooting, setup issues, technical problems
- **Tools**: All document search tools

## Troubleshooting

### FAISS/Vector Store Errors

```bash
# Reinstall FAISS
unset VIRTUAL_ENV && uv pip install --force-reinstall faiss-cpu
```

### Test Failures

```bash
# Run with verbose output
unset VIRTUAL_ENV && uv run --env-file .env pytest -v -s

# Check for API key in integration tests
# Integration tests require valid OPENAI_API_KEY
```

## Performance Optimization

### For Faster Responses

1. **Use gpt-4o-mini** for faster, cheaper responses:
   ```bash
   MODEL_NAME=gpt-4o-mini
   ```

2. **Reduce chunk size** in tools.py:
   ```python
   chunk_size=500  # Instead of 1000
   ```

3. **Limit search results**:
   ```python
   results = kb_manager.search(query, k=3)  # Instead of k=5
   ```

## Adding Custom Knowledge

### Adding PDF Documentation

1. Download Meta Quest PDFs from official sources
2. Place in `knowledge/` directory
3. Restart the agent to re-index

### Supported Document Formats

- PDF (.pdf) - Primary format
- Text (.txt) - Development/testing

### Knowledge Base Best Practices

- Use official Meta Quest documentation
- Keep PDFs well-organized
- Name files descriptively
- Update regularly with new documentation
- Remove outdated files

## Development

### Adding New Agents

Edit `src/agents.py`:

```python
def custom_agent(self) -> Agent:
    return Agent(
        role="Custom Role",
        goal="Custom goal",
        backstory="Custom backstory",
        tools=META_QUEST_TOOLS,
        allow_delegation=False,
        verbose=self.verbose,
        llm=self.model_name,
    )
```

### Adding New Tools

Edit `src/tools.py`:

```python
@tool
def custom_tool(query: str) -> str:
    """Tool description for LLM."""
    # Implementation
    return result
```

### Adding New Scenarios

Create JSON file in `src/scenarios/`:

```json
{
  "name": "Custom Scenario",
  "description": "Description",
  "conversation": [
    {
      "user": "Question",
      "expected": {
        "message_contains": ["keyword"]
      }
    }
  ]
}
```

## Resources

- **CrewAI Documentation**: https://docs.crewai.com/
- **Meta Quest Support**: https://www.meta.com/help/quest/
- **LangChain Documentation**: https://python.langchain.com/
- **OpenAI API**: https://platform.openai.com/docs/

**Built with CrewAI** - Multi-agent orchestration for AI applications
