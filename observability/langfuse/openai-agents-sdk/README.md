# OpenAI Agents SDK with Langfuse Observability

This directory contains fully instrumented versions of OpenAI Agents SDK demos with comprehensive Langfuse tracing.

## Available Demos

### Financial Research Agent Demo
**Path**: `financial-research-agent-demo/`

A multi-agent financial research system with 6 specialized agents, 4 tools, and complete observability.

**Features**:
- ✅ Complete workflow tracing (query → report)
- ✅ Individual agent execution traces (planner, search, writer, etc)
- ✅ Tool-level observability (search, financials, risk analysis, market data)
- ✅ Concurrent execution tracking (parallel searches)
- ✅ Token usage and cost tracking
- ✅ Error tracking at all levels
- ✅ User session tracking

**Quick Start**:
```bash
cd financial-research-agent-demo
unset VIRTUAL_ENV && uv sync
cp .env.example .env
# Add your API keys to .env
uv run --env-file .env python -m src.manager "Analyze Apple Inc"
```

**Compare With Untraced**:
- Original: `frameworks/openai-agents-sdk/financial-research-agents-demo`
- Traced: `observability/langfuse/openai-agents-sdk/financial-research-agent-demo`

## What You'll Learn

By using these traced implementations, you'll understand:

1. **Multi-Agent Observability**
   - How to trace agent workflows end-to-end
   - Context propagation between agents
   - Performance profiling per agent

2. **Tool Instrumentation**
   - Tracking tool invocations
   - Capturing inputs and outputs
   - Measuring tool performance

3. **Production Monitoring**
   - Token usage tracking
   - Cost attribution per agent
   - Error rates and debugging
   - Performance bottlenecks

4. **Implementation Patterns**
   - Non-invasive `@observe` decorators
   - Async tracing support
   - Nested span hierarchies
   - Rich metadata capture

## Langfuse Features Demonstrated

- ✅ Trace hierarchy (workflow → agents → tools → generations)
- ✅ Concurrent execution tracking
- ✅ Custom metadata at all levels
- ✅ Input/output capture
- ✅ Error tracking with context
- ✅ Token usage and costs
- ✅ User and session tracking
- ✅ Performance metrics

## Prerequisites

1. **OpenAI API Key**: Required for agent execution
2. **Langfuse Account**: Get free account at [cloud.langfuse.com](https://cloud.langfuse.com)
3. **Python 3.11+**: Required by OpenAI Agents SDK
4. **uv**: For dependency management

## Documentation

Each demo includes:
- `README.md` - Usage instructions and examples
- `OBSERVABILITY_SUMMARY.md` - Implementation details
- `.env.example` - Configuration template

## Resources

- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse Python SDK](https://langfuse.com/docs/sdk/python)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [Multi-Agent Tracing Guide](https://langfuse.com/docs/tracing)
