## Google ADK Agent Deepeval Runner

A standalone [uv](https://docs.astral.sh/uv/) project that executes the Google ADK Code Debug Agent scenarios and scores every turn with [DeepEval](https://deepwiki.com/confident-ai/deepeval) metrics. The runner reuses the agents and scenario JSON files from `frameworks/google-adk/code-debug-agent-demo` and emits structured JSON reports you can share with Langfuse/LangSmith traces.

> **Docs used:** DeepEval metric APIs were referenced through the Context7 DeepEval docset (mirrors the official docs at `deepwiki.com/confident-ai/deepeval`) plus the public repository (`confident-ai/deepeval`).

### Prerequisites

- Python 3.11+
- `uv` CLI (`pip install uv` or download a release binary)
- Access to the agent repo under `frameworks/google-adk/code-debug-agent-demo`

### Setup

1. **Copy the environment template and configure your API keys:**

```bash
cp env.example .env
```

Then edit `.env` and add your credentials:
- **Required:** `GOOGLE_API_KEY` - Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Optional:** `CONFIDENT_API_KEY` - Your Confident AI API key to automatically upload evaluation results to the platform
- **Optional:** `STACKEXCHANGE_KEY` - Get from [Stack Apps](https://stackapps.com/apps/oauth/register) for higher search quotas
- **Optional:** `OPENAI_API_KEY` - For DeepEval metrics that use OpenAI models
- **Optional:** Langfuse keys (`LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`) for observability
- **Optional:** LangSmith keys (`LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`) for observability

2. **Install dependencies:**

```bash
unset VIRTUAL_ENV && uv sync
```

The project depends on `deepeval`, `google-adk`, Langfuse/LangSmith SDKs, and the agent's Google Cloud dependencies, so the first sync may take a minute.

### Usage

List bundled scenarios (mirrors the `src/scenarios/` directory from the agent repo):

```bash
unset VIRTUAL_ENV && uv run python -m google_adk_deepeval_run --list-scenarios
```

Run DeepEval against ALL scenario files in the scenarios directory:

```bash
unset VIRTUAL_ENV && uv run python -m google_adk_deepeval_run --all-scenarios
```

Run all scenarios with a specific agent:

```bash
unset VIRTUAL_ENV && uv run python -m google_adk_deepeval_run --all-scenarios --agent-name quick_debug_agent
```

Run DeepEval against a specific scenario file:

```bash
unset VIRTUAL_ENV && uv run python -m google_adk_deepeval_run \
  --scenario-file ../frameworks/google-adk/code-debug-agent-demo/src/scenarios/python_import_error_missing_module.json \
  --agent-name debug_agent
```

The `.env` file in the project root will be automatically loaded. You can also specify additional env files:

```bash
unset VIRTUAL_ENV && uv run python -m google_adk_deepeval_run \
  --scenario-file scenarios.json \
  --env-file /path/to/custom.env
```

Key flags:

- `--all-scenarios` (or `--all`): runs ALL scenario JSON files in the scenarios directory.
- `--scenario-file`: JSON path (defaults to the sample import error scenario).
- `--agent-name`: runs a specific agent registered in `src/agents.py` (e.g., `quick_debug_agent`).
- `--reports-dir`: where to save DeepEval JSON (defaults to `reports/`).
- `--env-file`: repeatable flag for extra `.env` files (useful for separating Langfuse/LangSmith tokens).

Each run emits a `*_deepeval_<timestamp>.json` report that includes:

- Raw Google ADK runner status (tools invoked, messages, timing, errors)
- Per-turn DeepEval metric outcomes (keyword coverage, link checks, tool usage)
- Aggregated pass rates so you can gate CI or dashboards

### Confident AI Integration

When you set the `CONFIDENT_API_KEY` environment variable, evaluation results are automatically uploaded to your [Confident AI](https://app.confident-ai.com) dashboard. This provides:

- **Visual dashboards** - View evaluation metrics, success rates, and trends over time
- **Collaboration** - Share results with your team and track improvements
- **Historical tracking** - Compare runs to identify regressions or improvements
- **Detailed analysis** - Drill down into individual test cases and metric failures

To enable:

```bash
export CONFIDENT_API_KEY="your_api_key_here"
```

After running evaluations, visit [app.confident-ai.com](https://app.confident-ai.com) to view your results in the **moyai-org** organization.

**Note:** By default, the browser opening behavior is disabled to prevent interruptions during batch scenario runs. If you want to enable automatic browser opening after each result upload, set:

```bash
export CONFIDENT_OPEN_BROWSER="true"
```

### Extending

- Add new scenario JSON files under `frameworks/google-adk/code-debug-agent-demo/src/scenarios`.
- Implement richer DeepEval metrics in `src/google_adk_deepeval_run/evaluators/metrics.py` (e.g., hallucination, groundedness) using the Context7 docs as references.
- Integrate Langfuse/LangSmith exporters by reading the JSON reports inside `reports/`.

### Tests

```bash
unset VIRTUAL_ENV && uv run pytest
```

The suite only exercises the custom DeepEval metrics and scenario discovery helpers, so it runs quickly and does not hit the Gemini API.
