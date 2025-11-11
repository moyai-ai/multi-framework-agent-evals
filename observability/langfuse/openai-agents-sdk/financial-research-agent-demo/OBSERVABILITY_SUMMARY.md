# Langfuse Observability Implementation Summary

## Overview

This is a fully instrumented version of the OpenAI Agents SDK financial research agent demo with complete Langfuse tracing.

## What Was Added

### 1. Langfuse SDK Integration

**Dependencies** (`pyproject.toml`):
- Added `langfuse>=2.0.0` to dependencies

**Environment Variables** (`.env.example`):
- `LANGFUSE_PUBLIC_KEY` - Langfuse public key
- `LANGFUSE_SECRET_KEY` - Langfuse secret key
- `LANGFUSE_HOST` - Langfuse instance URL (optional)

### 2. Context Enhancements

**File**: `src/context.py`

Added tracing fields to `FinancialResearchContext`:
- `trace_id` - Langfuse trace identifier
- `user_id` - User identifier for filtering
- `parent_observation_id` - For nested observations

### 3. Tool-Level Tracing

**File**: `src/tools.py`

All 4 tools now include:
- `@observe(as_type="tool")` decorator
- Input/output capture via `langfuse.update_current_observation()`
- Rich metadata (tool type, company name, query details)

**Traced Tools**:
1. `web_search_tool` - Search execution
2. `company_financials_tool` - Financial analysis
3. `risk_analysis_tool` - Risk assessment  
4. `market_data_tool` - Market data retrieval

### 4. Workflow-Level Tracing

**File**: `src/manager.py`

**Complete workflow instrumentation**:
- `@observe(name="financial_research_workflow")` on `run()` method
- `@observe(name="plan_searches", as_type="chain")` for planning
- `@observe(name="perform_searches", as_type="chain")` for concurrent searches
- `@observe(name="search_single_term", as_type="agent")` per search
- `@observe(name="write_report", as_type="agent")` for report generation
- `@observe(name="verify_report", as_type="agent")` for verification

**Trace metadata** includes:
- User ID and session tracking
- Agent count and framework info
- Stage completion tracking
- Error information on failures

### 5. Test Scenario Tracing

**File**: `src/runner.py`

Enhanced scenario runner with:
- `@observe(name="run_test_scenario")` decorator
- Trace URLs in report output
- Scenario metadata in traces
- Langfuse URL generation per scenario

## Trace Hierarchy

```
📊 Trace: financial_research_workflow
├─ 📋 Chain: plan_searches
│  └─ Planner Agent execution
├─ 🔗 Chain: perform_searches
│  ├─ Agent: search_single_term (Term 1)
│  │  └─ Tool: web_search_tool
│  ├─ Agent: search_single_term (Term 2)
│  │  └─ Tool: web_search_tool
│  └─ Agent: search_single_term (Term 3)
│     └─ Tool: web_search_tool
├─ 📝 Agent: write_report
│  ├─ Tool: company_financials_tool
│  ├─ Tool: risk_analysis_tool
│  └─ Writer Agent LLM call
└─ ✅ Agent: verify_report
   └─ Verifier Agent LLM call
```

## Observable Components

### Context Providers

1. **Tools** (4 total):
   - Each tool call creates a "tool" type span
   - Inputs and outputs fully captured
   - Execution time tracked

2. **Sub-Agents** (6 total):
   - Planner Agent - search strategy
   - Search Agent - concurrent searches  
   - Financials Analyst - financial metrics
   - Risk Analyst - risk assessment
   - Writer Agent - report synthesis
   - Verifier Agent - quality validation

3. **RAG-like Pattern**:
   - Search results act as retrieval context
   - Analyst tools provide specialized knowledge
   - All retrievals traced

### Observability Levels

1. **Trace Level**:
   - User query
   - Total execution time
   - All stages
   - Final verification status

2. **Agent Level**:
   - Individual agent execution
   - Agent name and role
   - Input/output per agent
   - LLM parameters and usage

3. **Tool Level**:
   - Tool invocations
   - Tool parameters
   - Results returned
   - Performance per tool

4. **Generation Level**:
   - LLM calls (automatic via SDK)
   - Token usage
   - Costs
   - Model parameters

## Key Instrumentation Patterns

### 1. Decorator Pattern
```python
from langfuse import observe, get_client

@observe(as_type="tool")
async def web_search_tool(query: str) -> str:
    langfuse = get_client()
    langfuse.update_current_observation(
        metadata={"query": query},
        input={"query": query}
    )
    # ... tool logic ...
    langfuse.update_current_observation(
        output={"results": output}
    )
    return output
```

### 2. Nested Tracing
```python
@observe(name="financial_research_workflow")
async def run(self, query: str):
    # Top-level trace
    search_plan = await self._plan_searches(query)  # Nested span
    search_results = await self._perform_searches(search_plan)  # Nested span
    # ...
```

### 3. Concurrent Tracing
```python
@observe(name="perform_searches", as_type="chain")
async def _perform_searches(self, search_terms):
    tasks = [self._search(term) for term in search_terms]
    results = await asyncio.gather(*tasks)
    # Each task creates its own traced span
```

## Usage Examples

### Run with Tracing
```bash
# Set up environment
export OPENAI_API_KEY=sk-...
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...

# Run interactive
uv run --env-file .env python -m src.manager "Analyze Apple Inc"

# Output includes trace URL:
# 📊 Trace ID: trace-abc123...
# View your trace: https://cloud.langfuse.com/trace/trace-abc123...
```

### Run Scenarios with Tracing
```bash
# Single scenario
uv run --env-file .env python -m src.runner src/scenarios/company_analysis.json -v

# All scenarios
uv run --env-file .env python -m src.runner --all-scenarios -v
```

## Learning Outcomes

By comparing this traced version with the untraced original, you can learn:

1. **Tool Usage Patterns**: See which agents use which tools and how often
2. **Performance Bottlenecks**: Identify slow agents or tools
3. **Concurrent Execution**: Visualize parallel search execution
4. **Token Costs**: Track LLM usage per agent
5. **Error Propagation**: See where failures occur and how they propagate
6. **Agent Interactions**: Understand data flow between agents

## Production Considerations

This implementation demonstrates:
- ✅ Non-invasive instrumentation (decorators)
- ✅ Minimal code changes
- ✅ Automatic context propagation
- ✅ Error tracking at all levels
- ✅ Performance monitoring
- ✅ Cost tracking

For production use:
1. Replace mock tools with real APIs (tracing will work unchanged)
2. Add user authentication for user_id tracking
3. Set up Langfuse alerts for failures
4. Use custom evaluations for quality monitoring
5. Implement caching for expensive operations

## Files Modified/Created

### Modified from Original
- `src/context.py` - Added trace_id fields
- `src/tools.py` - Added @observe decorators
- `src/agents.py` - No changes (tracing handled at manager level)
- `src/manager.py` - Added complete workflow tracing
- `src/runner.py` - Added scenario-level tracing

### New Files
- `.env.example` - Langfuse credentials template
- `OBSERVABILITY_SUMMARY.md` - This file

### Dependencies
- `pyproject.toml` - Added langfuse>=2.0.0

## Comparison: Before vs After

### Before (Untraced)
```
User Query → [Black Box] → Report
- No visibility into agent execution
- No tool usage tracking
- No performance metrics
- Debugging requires print statements
```

### After (Traced)
```
User Query → [Fully Visible Workflow] → Report
- Complete agent execution visibility
- All tool calls tracked
- Performance metrics at every level
- Visual debugging in Langfuse UI
- Token usage and costs
- Error tracking with context
```

## Next Steps

1. **Run both versions** side-by-side with same query
2. **Compare Langfuse dashboard** vs terminal output
3. **Analyze performance** - which agents are slowest?
4. **Test error scenarios** - break a tool, see trace
5. **Experiment with modifications** - add new tools, see traces update

## Resources

- Original (untraced): `frameworks/openai-agents-sdk/financial-research-agents-demo`
- Traced version: `observability/langfuse/openai-agents-sdk/financial-research-agent-demo`
- Langfuse Docs: https://langfuse.com/docs
- OpenAI Agents SDK: https://openai.github.io/openai-agents-python/
