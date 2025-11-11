# Langfuse Trace Identification Guide

**Test Run Timestamp**: 2025-11-11 11:33:48
**Test Run ID**: `demo_run_20251111_113348`
**User ID**: `demo_user_20251111_113348`

## Quick Access to Langfuse Dashboard

🔗 **Langfuse Dashboard**: https://cloud.langfuse.com

## How to Find Your Traces

### Method 1: Filter by Test Run (See All 3 Scenarios)

In the Langfuse dashboard:

1. Go to **Traces** tab
2. Click on **Filters**
3. Add filter: **Session ID** contains `demo_run_20251111_113348`
4. Or filter by **User ID** equals `demo_user_20251111_113348`

This will show all 3 scenario traces from this test run.

### Method 2: Filter by Individual Scenario

#### Scenario 1: Python Pandas ImportError

**Identifiers:**
- Session ID: `demo_run_20251111_113348_scenario_1`
- User ID: `demo_user_20251111_113348`
- Agent: `debug_agent`
- Tags: `demo`, `python`, `import-error`, `google-adk`, `debug-agent`

**Prompt**: "I am getting this error: ImportError: No module named pandas. How do I install pandas?"

**Expected in Trace:**
- Trace Name: "Agent Execution: debug_agent"
- Tool Call: `search_stack_exchange_for_error`
- Retriever: `search_similar_errors`
- Response: Error analysis and installation instructions

---

#### Scenario 2: JavaScript Map TypeError

**Identifiers:**
- Session ID: `demo_run_20251111_113348_scenario_2`
- User ID: `demo_user_20251111_113348`
- Agent: `quick_debug_agent`
- Tags: `demo`, `javascript`, `type-error`, `google-adk`, `debug-agent`

**Prompt**: "TypeError: Cannot read property map of undefined. What does this mean and how do I fix it?"

**Expected in Trace:**
- Trace Name: "Agent Execution: quick_debug_agent"
- Tool Call: `search_stack_exchange_for_error`
- Retriever: `search_similar_errors`
- Response: Quick explanation and fix

---

#### Scenario 3: React Hooks Error

**Identifiers:**
- Session ID: `demo_run_20251111_113348_scenario_3`
- User ID: `demo_user_20251111_113348`
- Agent: `debug_agent`
- Tags: `demo`, `react`, `hooks`, `google-adk`, `debug-agent`

**Prompt**: "React Hook useState is called conditionally. React Hooks must be called in the exact same order"

**Expected in Trace:**
- Trace Name: "Agent Execution: debug_agent"
- Tool Call: `search_stack_exchange_for_error`
- Retriever: `search_similar_errors`
- Response: React Hooks rules explanation and fix

---

### Method 3: Filter by Tags

Use these tag filters in Langfuse:

- **`demo`** - All demo scenarios from this test run
- **`google-adk`** - All Google ADK agent traces (automatically added)
- **`debug-agent`** - All debug agent traces (automatically added)
- **`python`** - Python-related scenarios
- **`javascript`** - JavaScript-related scenarios
- **`react`** - React-related scenarios

## Expected Trace Structure

When you click on any trace, you should see this hierarchy:

```
📊 Trace: "Agent Execution: [agent_name]"
│
├── 📋 Metadata
│   ├── User ID: demo_user_20251111_113348
│   ├── Session ID: demo_run_20251111_113348_scenario_X
│   ├── Tags: [demo, google-adk, debug-agent, ...]
│   └── Agent Name: debug_agent or quick_debug_agent
│
├── 🤖 Span: debug_agent_execution (type: agent)
│   ├── Input:
│   │   ├── prompt: "[The error message]"
│   │   └── agent: "debug_agent"
│   │
│   ├── Output:
│   │   ├── total_events: [number]
│   │   └── response_summary: "[First few events]"
│   │
│   ├── Metadata:
│   │   ├── agent_model: "gemini-2.0-flash-exp"
│   │   ├── events_processed: [number]
│   │   └── execution_completed: true
│   │
│   ├── 🔧 Span: search_stack_exchange_for_error (type: tool)
│   │   ├── Input:
│   │   │   ├── error_message: "[The error]"
│   │   │   ├── programming_language: "python/javascript"
│   │   │   ├── include_solutions: true
│   │   │   └── max_results: [number]
│   │   │
│   │   ├── Output:
│   │   │   ├── success: true
│   │   │   ├── total_results: [number]
│   │   │   └── results: [Array of Stack Exchange results]
│   │   │
│   │   └── 📚 Span: search_similar_errors (type: retriever)
│   │       ├── Input:
│   │       │   ├── error_message: "[The error]"
│   │       │   ├── programming_language: "python/javascript"
│   │       │   └── limit: [number]
│   │       │
│   │       └── Output:
│   │           ├── success: true
│   │           ├── results: [Array of similar errors]
│   │           └── total_results: [number]
│   │
│   └── 📝 Span: _format_debug_response (callback)
│       ├── Output:
│       │   ├── response_preview: "[First 500 chars]"
│       │   └── response_length: [number]
│       │
│       └── Metadata:
│           └── formatting_applied: true
```

## What to Look For in Each Trace

### 1. Agent Execution Span (Top Level)

**Type**: `agent`

**Key Metrics:**
- Total execution time
- Number of events processed
- Final response summary

**Metadata:**
- Agent model (should be "gemini-2.0-flash-exp")
- Execution status (completed/error)

### 2. Tool Call Spans

**Type**: `tool`

**Tool Names:**
- `search_stack_exchange_for_error` - Main error search tool
- `search_stack_exchange_general` - General search (if used)
- `get_stack_exchange_answers` - Answer retrieval (if used)
- `analyze_error_and_suggest_fix` - Error analysis (if used)

**What to Check:**
- Input parameters (error message, language, framework)
- Output (success status, number of results)
- Execution time

### 3. Retriever Spans (RAG Operations)

**Type**: `retriever`

**Retriever Names:**
- `search_similar_errors` - Searches Stack Exchange for similar errors
- `search_questions` - General question search
- `get_answers` - Fetches specific answers

**What to Check:**
- Search queries and keywords
- Number of results retrieved
- Retrieval latency
- Stack Exchange API quota usage

### 4. Callback Spans

**Callback Functions:**
- `_format_debug_response` - Response formatting

**What to Check:**
- Response length
- Preview of formatted content
- Any formatting errors

## Performance Metrics to Analyze

### Execution Time Breakdown

Look at the duration of each span:

1. **Total Trace Duration**: End-to-end execution time
2. **Agent Span Duration**: Agent orchestration overhead
3. **Tool Span Duration**: Time spent calling tools
4. **Retriever Span Duration**: RAG/search operation time

**Expected Times:**
- Total execution: 2-5 seconds
- Tool calls: 1-3 seconds each
- Retriever operations: 0.5-2 seconds each
- Overhead (Langfuse): <10ms per span

### Tool Usage Patterns

**For `debug_agent`:**
- Usually calls `search_stack_exchange_for_error`
- May call multiple tools per query
- Provides comprehensive responses

**For `quick_debug_agent`:**
- Calls fewer tools (optimized for speed)
- Focuses on quick error lookup
- Provides concise responses

## Comparing Agents

Use the traces to compare `debug_agent` vs `quick_debug_agent`:

### Debug Agent (Scenarios 1 & 3)
- More comprehensive tool usage
- Longer execution time
- More detailed responses
- Better for complex errors

### Quick Debug Agent (Scenario 2)
- Faster execution
- Fewer tool calls
- Concise responses
- Better for simple errors

## Troubleshooting

### If Traces Don't Appear

1. **Wait 30-60 seconds** - Traces can take time to upload
2. **Check filters** - Clear all filters and search by User ID
3. **Refresh the page** - Sometimes needed to see new data
4. **Check Langfuse status** - Visit https://status.langfuse.com

### If Trace Data is Missing

1. **Check span hierarchy** - Expand all spans to see nested data
2. **Look at metadata** - Click "Show metadata" on each span
3. **Check input/output** - May be collapsed by default
4. **Verify environment** - Ensure LANGFUSE_TRACING_ENABLED=true

## Learning Exercises

### Exercise 1: Compare Tool Usage
1. Open Scenario 1 (debug_agent) trace
2. Open Scenario 2 (quick_debug_agent) trace
3. Compare:
   - Number of tool calls
   - Which tools were used
   - Execution time differences

### Exercise 2: Analyze RAG Operations
1. Find the `search_similar_errors` retriever span
2. Look at:
   - What keywords were extracted from the error?
   - How many results were retrieved?
   - What was the retrieval latency?
3. Compare across different scenarios

### Exercise 3: Track User Journey
1. Filter by User ID: `demo_user_20251111_113348`
2. See all 3 scenarios in chronological order
3. Analyze:
   - Which agent performed better?
   - Which errors took longer to resolve?
   - Pattern of tool usage across queries

### Exercise 4: Performance Optimization
1. Sort traces by duration (longest first)
2. Identify the slowest operation
3. Check if it's:
   - Stack Exchange API latency?
   - LLM response time?
   - Tool processing overhead?

## Advanced Filtering Examples

### Find All Error Cases
```
Tags: contains "error"
Status: error
```

### Find Slow Executions
```
Duration: > 5000ms
```

### Find Specific User's Traces
```
User ID: equals "demo_user_20251111_113348"
```

### Find Recent Demo Traces
```
Tags: contains "demo"
Timestamp: last 1 hour
```

## Export and Share

### Export Trace Data
1. Click on a trace
2. Click "Export" button
3. Download as JSON for analysis

### Share Trace with Team
1. Click on a trace
2. Copy the URL from browser
3. Share the link (requires Langfuse access)

## Next Steps

1. ✅ View the 3 traces in Langfuse dashboard
2. ✅ Explore the span hierarchy
3. ✅ Compare agent performance
4. ✅ Analyze tool usage patterns
5. ✅ Check RAG retrieval effectiveness
6. ✅ Set up custom dashboards in Langfuse
7. ✅ Run more scenarios with different errors

---

**Generated**: 2025-11-11 11:33:48
**Test Run**: demo_run_20251111_113348
**Scenarios**: 3/3 passed successfully
**Dashboard**: https://cloud.langfuse.com
