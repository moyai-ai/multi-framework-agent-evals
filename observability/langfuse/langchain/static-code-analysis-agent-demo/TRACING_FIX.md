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

Create a trace with metadata, then create `CallbackHandler` with `root=trace`:

```python
# ✅ CORRECT - Create trace first, then handler rooted at that trace

# 1. Set environment variables
import os
os.environ["LANGFUSE_PUBLIC_KEY"] = config.LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = config.LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_HOST"] = config.LANGFUSE_HOST

# 2. Get Langfuse client
from langfuse import get_client
langfuse_client = get_client()

# 3. Create trace with all metadata
trace = langfuse_client.trace(
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

# 4. Create CallbackHandler rooted at this trace
from langfuse.langchain import CallbackHandler
langfuse_handler = CallbackHandler(root=trace)

# 5. Use handler with LangChain
response = chain.invoke(
    {"input": "..."},
    config={"callbacks": [langfuse_handler]}
)
```

**Key Points:**
- Create trace with `langfuse_client.trace()` and all metadata upfront
- Pass `root=trace` to `CallbackHandler` constructor
- This ensures trace has correct name, user_id, session_id, tags, metadata from the start
- The `root` parameter links the LangChain execution to the Langfuse trace

## Changes Made

### 1. Create Trace with Metadata, Then Create Handler

**File:** `src/agent/graph.py:475-480` (env vars), `src/agent/graph.py:392-395` (client), `src/agent/graph.py:420-433` (trace and handler)

- Set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` environment variables
- Get Langfuse client with `get_client()`
- Build trace name, tags, metadata, user_id, session_id upfront
- Create trace with `langfuse_client.trace(name=..., user_id=..., session_id=..., tags=..., metadata=..., version=...)`
- Create `CallbackHandler(root=trace)` to link LangChain execution to the trace

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
2. `36e4b97` - Fix trace naming by setting metadata in CallbackHandler constructor (incorrect - constructor doesn't accept trace_name)
3. `da8a6ab` - Fix: use set_trace_params() instead of constructor parameters (incorrect - set_trace_params doesn't exist)
4. `714b35d` - Fix: CallbackHandler reads credentials from environment (incorrect - still missing root parameter)
5. `5404a05` - Fix: use langfuse_client.trace() with root parameter ✅ **CORRECT**
