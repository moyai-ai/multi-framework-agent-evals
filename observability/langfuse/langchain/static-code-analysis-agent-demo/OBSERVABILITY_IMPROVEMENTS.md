# Langfuse Observability Improvements

## Current State Analysis

Based on the trace JSON export, here's what's currently being captured:

### ✅ What's Working Well

1. **Basic Trace Structure**
   - Top-level trace name: "LangGraph"
   - Input/output captured for entire graph execution
   - Thread ID in metadata for session tracking
   - OpenTelemetry resource attributes present

2. **LLM Call Tracking**
   - All 3 LLM calls per analysis are captured
   - Token usage tracked (input, output, total)
   - Model details (gpt-4-0125-preview)
   - Tool calls captured with arguments

3. **Tool Execution Tracking**
   - Tool results captured as messages
   - Success status indicated
   - Tool outputs properly formatted

### ❌ What's Missing

Based on Langfuse documentation and best practices:

1. **No User Tracking**
   - `userId`: Not set
   - User-specific analytics unavailable
   - Cannot track per-user costs or usage patterns

2. **No Session Management**
   - `sessionId`: Not set (only thread_id in metadata)
   - Cannot group multiple analyses by user session
   - Difficult to track conversation flows

3. **No Tags**
   - `tags`: Empty array
   - Cannot filter/search traces by:
     - Analysis type (security, quality, dependencies)
     - Environment (dev, staging, prod)
     - Issue severity
     - Success/failure status

4. **Limited Metadata**
   - Missing business context:
     - Repository details not in metadata
     - Analysis configuration not captured
     - Issue severity distribution
     - Analysis duration

5. **No Custom Spans for Graph Nodes**
   - Reasoning node: No explicit span
   - Action node: No explicit span
   - Observation node: No explicit span
   - Report node: No explicit span
   - Cannot analyze time spent in each node

6. **No Scores/Evaluations**
   - No quality scores for analysis
   - No user feedback captured
   - No automated evaluation metrics

7. **No Version Tracking**
   - `version`: Not set
   - Cannot compare different model/config versions
   - Difficult to track changes over time

## Recommended Improvements

### Priority 1: Essential Tracking

#### 1. Add Session and User IDs

```python
# In run_agent() function
async def run_agent(
    repository_url: str,
    analysis_type: str = "security",
    config: Optional[Config] = None,
    user_id: Optional[str] = None,  # NEW
    session_id: Optional[str] = None  # NEW
) -> Dict[str, Any]:

    if langfuse_handler:
        # Update trace with user and session info
        langfuse_client.update_current_trace(
            user_id=user_id or "anonymous",
            session_id=session_id or f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )
```

**Benefits:**
- Track usage per user
- Monitor costs per user
- Group related analyses
- Better debugging for user-specific issues

#### 2. Add Meaningful Tags

```python
# In run_agent() function
tags = [
    "static-analysis",
    analysis_type,  # "security", "quality", "dependencies"
    "langgraph",
    "production",  # or "development", "staging"
]

if final_state.get("error"):
    tags.append("error")
else:
    tags.append("success")

# Add severity tags based on issues found
severity_counts = {}
for issue in final_state.get("issues_found", []):
    severity = issue.get("severity", "UNKNOWN")
    severity_counts[severity] = severity_counts.get(severity, 0) + 1

if severity_counts.get("CRITICAL", 0) > 0:
    tags.append("has-critical-issues")
if severity_counts.get("HIGH", 0) > 0:
    tags.append("has-high-issues")

langfuse_client.update_current_trace(tags=tags)
```

**Benefits:**
- Easy filtering in Langfuse UI
- Quick identification of critical analyses
- Environment-based filtering
- Success/failure tracking

#### 3. Enrich Metadata

```python
# In run_agent() function
metadata = {
    "repository": {
        "url": repository_url,
        "owner": initial_state["repository_owner"],
        "name": initial_state["repository_name"]
    },
    "analysis": {
        "type": analysis_type,
        "model": config.MODEL_NAME,
        "temperature": config.TEMPERATURE,
        "max_steps": initial_state["max_steps"]
    },
    "results": {
        "files_analyzed": len(final_state["files_analyzed"]),
        "total_files": len(final_state["files_to_analyze"]),
        "issues_found": len(final_state["issues_found"]),
        "severity_breakdown": {
            "CRITICAL": sum(1 for i in final_state["issues_found"] if i.get("severity") == "CRITICAL"),
            "HIGH": sum(1 for i in final_state["issues_found"] if i.get("severity") == "HIGH"),
            "MEDIUM": sum(1 for i in final_state["issues_found"] if i.get("severity") == "MEDIUM"),
            "LOW": sum(1 for i in final_state["issues_found"] if i.get("severity") == "LOW"),
        }
    },
    "execution": {
        "steps_taken": final_state["current_step"],
        "completed": final_state["should_continue"] == False,
        "has_error": final_state.get("error") is not None
    }
}

langfuse_client.update_current_trace(metadata=metadata)
```

**Benefits:**
- Rich context for analysis
- Better debugging
- Performance tracking
- Business metrics visibility

### Priority 2: Enhanced Observability

#### 4. Add Custom Spans for Graph Nodes

```python
# Update reasoning_node, action_node, observation_node, report_node
async def reasoning_node(state: AgentState) -> AgentState:
    """Node for reasoning about the next action with Langfuse tracing."""
    span_context = None
    if langfuse_client:
        span_context = langfuse_client.start_as_current_span(
            name="reasoning-node",
            input={
                "current_step": state['current_step'],
                "files_to_analyze": len(state['files_to_analyze']),
                "files_analyzed": len(state['files_analyzed']),
                "issues_found": len(state['issues_found'])
            },
            metadata={
                "node_type": "reasoning",
                "step": state['current_step'],
                "max_steps": state['max_steps']
            }
        )
        span_context.__enter__()

    try:
        # Existing reasoning logic...

        if span_context:
            span_context.update(
                output={
                    "has_tool_calls": has_tools,
                    "tool_count": len(response.tool_calls) if has_tools else 0,
                    "should_continue": state["should_continue"]
                }
            )
    finally:
        if span_context:
            span_context.__exit__(None, None, None)
```

**Benefits:**
- Node-level performance analysis
- Bottleneck identification
- Step-by-step debugging
- Time distribution visualization

#### 5. Add Observation Node Span

```python
async def observation_node(state: AgentState) -> AgentState:
    """Node for observing results with enhanced tracing."""
    span_context = None
    if langfuse_client:
        span_context = langfuse_client.start_as_current_span(
            name="observation-node",
            input={
                "tool_messages_count": len([msg for msg in state["messages"] if isinstance(msg, ToolMessage)]),
                "current_issues": len(state["issues_found"]),
                "current_files_analyzed": len(state["files_analyzed"])
            },
            metadata={"node_type": "observation"}
        )
        span_context.__enter__()

    try:
        # Existing observation logic...

        if span_context:
            span_context.update(
                output={
                    "new_issues_found": new_issues_count,
                    "files_marked_analyzed": files_marked_count,
                    "total_progress": f"{len(state['files_analyzed'])}/{len(state['files_to_analyze'])}"
                }
            )
    finally:
        if span_context:
            span_context.__exit__(None, None, None)
```

#### 6. Add Report Generation Span

```python
async def report_node(state: AgentState) -> AgentState:
    """Node for generating final report with tracing."""
    span_context = None
    if langfuse_client:
        span_context = langfuse_client.start_as_current_span(
            name="report-generation",
            input={
                "files_analyzed": len(state["files_analyzed"]),
                "total_issues": len(state["issues_found"]),
                "analysis_type": state["analysis_type"]
            },
            metadata={
                "node_type": "report",
                "severity_summary": {...}  # Severity breakdown
            }
        )
        span_context.__enter__()

    try:
        # Generate report...

        if span_context:
            span_context.update(
                output={"report_length": len(state["final_answer"])}
            )
    finally:
        if span_context:
            span_context.__exit__(None, None, None)
```

### Priority 3: Quality & Feedback

#### 7. Add Automated Scores

```python
# After analysis completes
if langfuse_client:
    # Completeness score
    completeness = len(final_state["files_analyzed"]) / len(final_state["files_to_analyze"]) if final_state["files_to_analyze"] else 0
    langfuse_client.score_current_trace(
        name="analysis-completeness",
        value=completeness,
        data_type="NUMERIC",
        comment=f"Analyzed {len(final_state['files_analyzed'])} of {len(final_state['files_to_analyze'])} files"
    )

    # Efficiency score (issues per step)
    efficiency = len(final_state["issues_found"]) / final_state["current_step"] if final_state["current_step"] > 0 else 0
    langfuse_client.score_current_trace(
        name="analysis-efficiency",
        value=efficiency,
        data_type="NUMERIC",
        comment=f"{len(final_state['issues_found'])} issues found in {final_state['current_step']} steps"
    )

    # Severity score (higher for more critical issues)
    severity_score = (
        severity_counts.get("CRITICAL", 0) * 4 +
        severity_counts.get("HIGH", 0) * 3 +
        severity_counts.get("MEDIUM", 0) * 2 +
        severity_counts.get("LOW", 0) * 1
    ) / len(final_state["issues_found"]) if final_state["issues_found"] else 0

    langfuse_client.score_current_trace(
        name="issue-severity",
        value=severity_score,
        data_type="NUMERIC",
        comment="Average issue severity (1=LOW, 4=CRITICAL)"
    )
```

**Benefits:**
- Automated quality metrics
- Performance trends over time
- Regression detection
- Benchmark comparisons

#### 8. Add Version Tracking

```python
# In run_agent() function
langfuse_client.update_current_trace(
    version=f"v{config.MODEL_NAME.replace('gpt-', '')}_{config.TEMPERATURE}",
)
```

**Benefits:**
- A/B testing different models
- Track prompt changes
- Configuration comparison
- Regression tracking

## Implementation Priority

### Phase 1: Quick Wins (30 mins)
1. Add user_id and session_id parameters
2. Add basic tags (analysis type, environment, status)
3. Add version tracking

### Phase 2: Core Improvements (1 hour)
4. Enrich metadata with repository and results
5. Add custom spans for all graph nodes
6. Improve error tracking in spans

### Phase 3: Advanced Features (1 hour)
7. Add automated quality scores
8. Add detailed performance metrics
9. Implement feedback mechanism

## Expected Benefits

### For Development
- **Debugging**: Trace execution flow through graph nodes
- **Performance**: Identify slow nodes/operations
- **Errors**: Better error context and resolution

### For Production
- **Monitoring**: Real-time analysis quality tracking
- **Costs**: Per-user, per-repository cost tracking
- **Quality**: Automated quality metrics and alerting

### For Business
- **Analytics**: User behavior and usage patterns
- **ROI**: Cost per issue found, efficiency metrics
- **Insights**: Popular repositories, common issues

## Example Enhanced Trace Structure

```
Trace: static-code-analysis (v1.0.0)
├── User: user_123
├── Session: session_abc
├── Tags: [static-analysis, security, production, success, has-critical-issues]
├── Metadata:
│   ├── repository: {url, owner, name}
│   ├── analysis: {type, model, temperature}
│   ├── results: {files_analyzed, issues_found, severity_breakdown}
│   └── execution: {steps_taken, completed, duration}
├── Scores:
│   ├── analysis-completeness: 1.0
│   ├── analysis-efficiency: 4.0
│   └── issue-severity: 3.5
└── Spans:
    ├── reasoning-node (Step 0) - 1.2s
    │   ├── LLM Call - 1.0s
    │   └── Output: {has_tool_calls: true, tool_count: 1}
    ├── action-node - 0.3s
    │   └── Tool: list_repository_files
    ├── observation-node - 0.1s
    │   └── Output: {new_issues: 0, files_marked: 0}
    ├── reasoning-node (Step 1) - 1.5s
    ├── action-node - 0.4s
    ├── observation-node - 0.1s
    ├── reasoning-node (Step 2) - 2.1s
    ├── action-node - 5.2s
    │   └── Tools: [run_opengrep_analysis × 3]
    ├── observation-node - 0.2s
    │   └── Output: {new_issues: 6, files_marked: 3}
    └── report-generation - 2.3s
        └── Output: {report_length: 1547}
```

## Next Steps

1. Review and prioritize improvements
2. Implement Phase 1 changes (quick wins)
3. Test with real analysis scenarios
4. Validate traces in Langfuse UI
5. Roll out to production
6. Set up dashboards and alerts
7. Collect user feedback
8. Iterate on improvements

## References

- [Langfuse Metadata Documentation](https://langfuse.com/docs/observability/features/metadata)
- [Langfuse Tags Documentation](https://langfuse.com/docs/observability/features/tags)
- [Langfuse Users Documentation](https://langfuse.com/docs/observability/features/users)
- [Langfuse Sessions Documentation](https://langfuse.com/docs/observability/features/sessions)
- [Langfuse Scores Documentation](https://langfuse.com/docs/observability/features/scores)
- [LangGraph Integration Guide](https://langfuse.com/docs/integrations/langgraph)
