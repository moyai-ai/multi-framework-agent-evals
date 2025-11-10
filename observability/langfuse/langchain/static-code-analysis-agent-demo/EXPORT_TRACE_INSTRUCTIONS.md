# How to Export Trace from Langfuse for Review

Since the programmatic API for exporting traces has some limitations, the easiest way to export a trace for review is through the Langfuse UI.

## Step 1: Access Langfuse UI

1. Go to [cloud.langfuse.com](https://cloud.langfuse.com)
2. Log in to your project
3. Navigate to **Traces** from the left sidebar

## Step 2: Find the Latest Trace

The latest trace should be at the top of the list. Look for:

**Trace Name**: `static-code-analysis-agent: security analysis - openai/openai-python`

**Details**:
- User: `anonymous`
- Session: `analysis_YYYYMMDD_HHMMSS`
- Tags: `static-analysis`, `security`, `langgraph`, `production`, `success`, `has-critical-issues`, `has-high-issues`
- Version: `vgpt-4-turbo-preview_0.3`

## Step 3: View Trace Details

1. Click on the trace to open the detailed view
2. You should see the trace hierarchy showing:
   - **Reasoning Node** spans (reasoning-node)
   - **Action Node** spans (action-node)
   - **Observation Node** spans (observation-node)
   - **LLM Generations** (from CallbackHandler - automatic)
   - **Tool Executions** (from CallbackHandler - automatic)

## Step 4: Export Trace

### Option 1: Export via UI (Recommended)

1. In the trace details view, look for an **Export** or **Download** button
2. Export as JSON format
3. Save the file (e.g., `trace_latest.json`)

### Option 2: Copy Trace Data

If export button is not available:

1. Right-click on the page
2. Select "Inspect" or "Developer Tools"
3. Go to the Network tab
4. Refresh the trace page
5. Look for API calls to get trace data
6. Copy the JSON response

### Option 3: Screenshot

If you can't export, take screenshots of:
1. Trace overview (showing name, tags, metadata)
2. Trace timeline/hierarchy (showing spans)
3. Individual span details (showing input/output)
4. LLM generation details (showing tokens, cost)

## Step 5: What to Review

When reviewing the trace, check for:

### ✅ Trace Identity
- [ ] Trace name is descriptive: `static-code-analysis-agent: security analysis - openai/openai-python`
- [ ] User ID is set correctly (`anonymous`)
- [ ] Session ID is generated
- [ ] Tags include: static-analysis, security, langgraph, production, success, severity tags
- [ ] Version is set: `vgpt-4-turbo-preview_0.3`

### ✅ Metadata
- [ ] Agent name: `static-code-analysis-agent`
- [ ] Demo name: `langchain-static-code-analysis-agent-demo`
- [ ] Agent version: `1.0.0`
- [ ] Repository information (url, owner, name)
- [ ] Analysis configuration (type, model, temperature, max_steps)
- [ ] Results breakdown (files analyzed, issues found, severity breakdown)
- [ ] Execution stats (steps taken, completion status)

### ✅ Phase 2: Node-Level Spans

Check that you see these custom spans:

1. **reasoning-node** spans
   - Input: current_step, files_to_analyze, files_analyzed, issues_found
   - Output: has_tool_calls, consecutive_no_tool_calls, should_continue

2. **action-node** spans
   - Input: current_step, tool_calls, num_tools
   - Output: tools_executed, num_results

3. **observation-node** spans
   - Input: current_step, files_analyzed, issues_found
   - Output: files_processed, new_issues, files_to_analyze

4. **report-node** spans
   - Input: files_analyzed, issues_found, analysis_type
   - Output: report_generated, report_length

### ✅ Automatic Tracing (CallbackHandler)

These should be automatically captured:

1. **LLM Generations**
   - Model: gpt-4-turbo-preview
   - Temperature: 0.3
   - Token usage (input, output, total)
   - Cost tracking

2. **Tool Executions**
   - list_repository_files
   - get_file_content
   - run_opengrep_analysis
   - summarize_findings

### ✅ Trace Hierarchy

The trace should show a clear hierarchy:

```
Trace: static-code-analysis-agent: security analysis - openai/openai-python
├── reasoning-node (span)
│   └── LLM Generation (automatic)
├── action-node (span)
│   ├── Tool: list_repository_files (automatic)
│   ├── Tool: get_file_content (automatic)
│   └── Tool: run_opengrep_analysis (automatic)
├── observation-node (span)
├── reasoning-node (span)
│   └── LLM Generation (automatic)
├── action-node (span)
│   └── [more tools...]
├── observation-node (span)
├── [... more cycles ...]
└── report-node (span)
    └── LLM Generation (automatic)
```

## Expected Improvements from Phase 2

Compare with the previous traces (before Phase 2) to verify:

### Before Phase 2
- Only automatic LLM and tool traces from CallbackHandler
- No visibility into reasoning/action/observation/report node logic
- Unclear which step failed or took too long

### After Phase 2
- ✅ Clear node-level visibility (reasoning, action, observation, report)
- ✅ Input/output tracking for each node
- ✅ Better debugging: can see which node has issues
- ✅ Performance tracking: can see which node takes longest
- ✅ Complete picture: manual spans + automatic LLM/tool traces

## Troubleshooting

### No Node-Level Spans Visible

If you don't see reasoning-node, action-node, observation-node, or report-node spans:

1. Check that Langfuse is enabled in .env: `LANGFUSE_ENABLED=true`
2. Verify credentials are correct
3. Re-run the analysis
4. Check for error messages in the console

### Spans Are Flat (No Hierarchy)

If spans are not nested properly:

1. This is a known issue with some Langfuse versions
2. The spans are still captured, just displayed flat
3. You can still see all the span data, it's just not nested visually

### Missing Automatic Traces

If you don't see LLM generations or tool executions:

1. Check that CallbackHandler is initialized correctly
2. Verify the handler is passed to LLM invocations
3. Check the console for any Langfuse errors

## Summary

Once you have the trace exported:

1. **Verify trace identity**: Name, user, session, tags, version, metadata
2. **Check Phase 2 spans**: reasoning-node, action-node, observation-node, report-node
3. **Verify automatic tracing**: LLM generations, tool executions
4. **Review hierarchy**: Spans are properly nested
5. **Assess improvements**: Better visibility than before Phase 2

Share the exported JSON or screenshots so I can verify the tracing is working as expected!
