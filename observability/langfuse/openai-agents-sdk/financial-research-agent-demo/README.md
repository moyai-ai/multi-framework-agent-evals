# OpenAI Agents SDK - Financial Research Multi-Agent Demo with Langfuse Tracing

A comprehensive demonstration of the OpenAI Agents SDK featuring a multi-agent financial research system with **full Langfuse observability**. This implementation showcases complete tracing of multi-agent workflows, tools, and context providers.

## Overview

This project implements a complete financial research agent system using the OpenAI Agents SDK **with comprehensive Langfuse instrumentation** for full observability.

## Key Features

- **Multi-agent orchestration** with specialized analyst agents (fully traced)
- **Concurrent execution** of search tasks (with individual traces)
- **Tool integration** for financial analysis (each tool call traced)
- **Complete observability** with Langfuse at every level

## Installation

```bash
cd observability/langfuse/openai-agents-sdk/financial-research-agent-demo
unset VIRTUAL_ENV && uv sync
cp .env.example .env
# Edit .env with your API keys
```

## Usage

Interactive research:
```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.manager "Analyze Apple Inc"
```

Run scenarios:
```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner --all-scenarios --verbose
```

## Comparing Traced vs Untraced

- **Untraced**: `frameworks/openai-agents-sdk/financial-research-agents-demo`
- **Traced**: `observability/langfuse/openai-agents-sdk/financial-research-agent-demo`

This implementation provides complete visibility into agent behavior, tool usage, performance metrics, and costs.
