# Langfuse Tracing Fix - Static Code Analysis Agent

## Problem

Traces were showing up in Langfuse UI as **"LangGraph"** instead of descriptive names like:
```
static-code-analysis-agent: security analysis - owner/repo
```

## Root Cause

The `CallbackHandler` was initialized without parameters:

```python
# ❌ WRONG - Creates trace with default name "LangGraph"
langfuse_handler = CallbackHandler()
```

The code tried to update the trace name **after** the agent finished:

```python
# This runs AFTER agent.ainvoke() completes
langfuse_client.update_current_trace(
    name=trace_name,
    user_id=user_id,
    tags=tags,
    ...
)
```

**Why this failed:** By the time `update_current_trace()` is called, the trace context has already been closed by LangChain, so the update doesn't work.

## Solution

Initialize `CallbackHandler` with credentials, then use `set_trace_params()` to set trace metadata:

```python
# ✅ CORRECT - Initialize handler then set trace params
langfuse_handler = CallbackHandler(
    public_key=config.LANGFUSE_PUBLIC_KEY,
    secret_key=config.LANGFUSE_SECRET_KEY,
    host=config.LANGFUSE_HOST
)

# Set trace metadata
langfuse_handler.set_trace_params(
    name="static-code-analysis-agent: security analysis - owner/repo",
    user_id=user_id or "anonymous",
    session_id=session_id or "session_id",
    tags=["static-analysis", "security", "langgraph", "production"],
    metadata={
        "agent": "static-code-analysis-agent",
        "demo_name": "langchain-static-code-analysis-agent-demo",
        "version": "1.0.0",
        "repository": {
            "url": repository_url,
            "owner": "owner",
            "name": "repo"
        },
        "analysis": {
            "type": "security",
            "model": "gpt-4-turbo-preview",
            "temperature": 0.3
        }
    },
    version="v1.0.0"
)
```

**Key Point:** The `CallbackHandler` constructor only accepts credentials. Use `set_trace_params()` method to set trace name, user_id, session_id, tags, and metadata.

## Changes Made

### 1. Initialize CallbackHandler with Credentials and Set Trace Params

**File:** `src/agent/graph.py:392-411`

- Build trace name, tags, metadata, user_id, session_id upfront
- Initialize `CallbackHandler` with credentials only
- Call `set_trace_params()` to set trace metadata

### 2. Remove Redundant update_current_trace()

**File:** `src/agent/graph.py:435-486`

- Removed ~100 lines of `update_current_trace()` code
- Replaced with lightweight result metadata update
- Now just adds scores and result metrics at the end

## Trace Naming Convention

Traces now follow this pattern:

```
static-code-analysis-agent: {analysis_type} analysis [{scenario_name}] - {owner/repo}
```

**Examples:**
- `static-code-analysis-agent: security analysis - facebook/react`
- `static-code-analysis-agent: security analysis [sql_injection] - owner/repo`
- `static-code-analysis-agent: quality analysis [code_quality] - vercel/next.js`

## Metadata Structure

Each trace includes:

```json
{
  "agent": "static-code-analysis-agent",
  "demo_name": "langchain-static-code-analysis-agent-demo",
  "version": "1.0.0",
  "scenario": "scenario_name",
  "repository": {
    "url": "https://github.com/owner/repo",
    "owner": "owner",
    "name": "repo"
  },
  "analysis": {
    "type": "security",
    "model": "gpt-4-turbo-preview",
    "temperature": 0.3
  },
  "results": {
    "files_analyzed": 5,
    "total_files": 10,
    "issues_found": 3,
    "severity_breakdown": {
      "CRITICAL": 1,
      "HIGH": 1,
      "MEDIUM": 1
    }
  }
}
```

## Tags

Each trace is tagged with:
- `static-analysis` - Agent type
- `{analysis_type}` - security/quality/dependencies
- `langgraph` - Framework
- `production` - Environment
- `scenario:{name}` - Scenario name (if applicable)
- `success` or `error` - Execution status (added at end)
- `has-critical-issues`, `has-high-issues` - Severity indicators (added at end)

## Testing

To verify the fix works:

### 1. Run a test analysis
```bash
cd observability/langfuse/langchain/static-code-analysis-agent-demo
uv run scripts/test_tracing.py
```

### 2. Check Langfuse UI
Traces should show as:
- `static-code-analysis-agent: security analysis [tracing_verification] - example/test-repo`
- `static-code-analysis-agent: quality analysis [quality_check] - example/test-repo`

### 3. Export and validate
```bash
uv run scripts/export_traces.py --name "static-code-analysis" --validate
```

## References

- [Langfuse CallbackHandler Docs](https://langfuse.com/docs/integrations/langchain/tracing)
- [LangChain Callback Documentation](https://python.langchain.com/docs/modules/callbacks/)

## Commits

1. `ce954f2` - Initial tracing improvements (removed manual spans)
2. `36e4b97` - Fix trace naming by setting metadata in CallbackHandler constructor (incorrect API)
3. `da8a6ab` - Fix: use set_trace_params() instead of constructor parameters (correct API)
