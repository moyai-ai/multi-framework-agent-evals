# Trace Naming and Scenario Tracking

This document explains how the agent uses descriptive trace names and scenario tracking for better observability in Langfuse.

## Problem Solved

Previously, traces appeared as generic "LangGraph" entries in Langfuse, making it difficult to:
- Identify which agent demo was running
- Distinguish between different analysis types
- Track specific test scenarios or evaluation runs
- Filter traces by scenario

## Solution

We now use **descriptive trace names** that include:
1. Agent demo name
2. Analysis type
3. Scenario name (optional)
4. Repository being analyzed

## Trace Name Format

```
static-code-analysis-agent: {analysis_type} analysis [{scenario_name}] - {owner}/{repo}
```

### Examples

**Without scenario:**
```
static-code-analysis-agent: security analysis - openai/openai-python
```

**With scenario:**
```
static-code-analysis-agent: security analysis [security-vulnerabilities-detection] - openai/openai-python
```

**Quality analysis:**
```
static-code-analysis-agent: quality analysis [code-style-check] - facebook/react
```

## Usage

### Command Line

```bash
# Basic usage (no scenario)
uv run --env-file .env python -m src.manager "https://github.com/openai/openai-python" \
  --type security

# With scenario name
uv run --env-file .env python -m src.manager "https://github.com/openai/openai-python" \
  --type security \
  --scenario "security-vulnerabilities-detection"

# Full observability (user, session, scenario)
uv run --env-file .env python -m src.manager "https://github.com/openai/openai-python" \
  --type security \
  --user-id "alice@example.com" \
  --session-id "sprint-review-2024-01" \
  --scenario "pre-release-security-audit"
```

### Python API

```python
from src.manager import AnalysisManager

manager = AnalysisManager()

# Basic analysis
result = await manager.analyze_repository(
    repository_url="https://github.com/openai/openai-python",
    analysis_type="security"
)

# With scenario tracking
result = await manager.analyze_repository(
    repository_url="https://github.com/openai/openai-python",
    analysis_type="security",
    scenario_name="security-vulnerabilities-detection"
)

# Full observability
result = await manager.analyze_repository(
    repository_url="https://github.com/openai/openai-python",
    analysis_type="security",
    user_id="alice@example.com",
    session_id="sprint-review-2024-01",
    scenario_name="pre-release-security-audit"
)
```

## Scenario Information in Metadata

The scenario name is tracked in multiple places:

### 1. Trace Name
Makes it immediately visible in the Langfuse trace list.

### 2. Tags
Scenario is added as a tag: `scenario:{scenario_name}`

Example tags:
```
["static-analysis", "security", "langgraph", "production",
 "scenario:security-vulnerabilities-detection", "success",
 "has-critical-issues", "has-high-issues"]
```

### 3. Metadata
Full scenario information is stored in metadata:

```json
{
  "agent": "static-code-analysis-agent",
  "demo_name": "langchain-static-code-analysis-agent-demo",
  "scenario": "security-vulnerabilities-detection",
  "repository": {
    "url": "https://github.com/openai/openai-python",
    "owner": "openai",
    "name": "openai-python"
  },
  "analysis": {
    "type": "security",
    "model": "gpt-4-turbo-preview",
    "temperature": 0.3,
    "max_steps": 20
  },
  "results": {
    "files_analyzed": 3,
    "total_files": 3,
    "issues_found": 12,
    "severity_breakdown": {
      "CRITICAL": 2,
      "HIGH": 10,
      "MEDIUM": 0,
      "LOW": 0
    }
  },
  "execution": {
    "steps_taken": 3,
    "completed": true,
    "has_error": false
  }
}
```

## Use Cases

### 1. Test Scenarios

Track specific test scenarios during evaluation:

```bash
# Test scenario 1: Security vulnerabilities
uv run --env-file .env python -m src.manager "https://github.com/example/repo" \
  --type security \
  --scenario "test-security-vulnerabilities"

# Test scenario 2: Code quality issues
uv run --env-file .env python -m src.manager "https://github.com/example/repo" \
  --type quality \
  --scenario "test-code-quality-issues"

# Test scenario 3: Dependency analysis
uv run --env-file .env python -m src.manager "https://github.com/example/repo" \
  --type dependencies \
  --scenario "test-dependency-vulnerabilities"
```

### 2. Evaluation Campaigns

Group related evaluations into sessions:

```bash
SESSION_ID="eval-campaign-2024-01"

for repo in "repo1" "repo2" "repo3"; do
  uv run --env-file .env python -m src.manager "https://github.com/example/$repo" \
    --type security \
    --session-id "$SESSION_ID" \
    --scenario "security-audit-jan-2024"
done
```

### 3. User-Specific Tracking

Track analyses by user and scenario:

```bash
uv run --env-file .env python -m src.manager "https://github.com/example/repo" \
  --type security \
  --user-id "alice@example.com" \
  --session-id "alice-analysis-session" \
  --scenario "pre-commit-security-check"
```

### 4. A/B Testing

Compare different configurations with scenario tags:

```bash
# Baseline configuration
uv run --env-file .env python -m src.manager "https://github.com/example/repo" \
  --type security \
  --scenario "ab-test-baseline"

# Experimental configuration (modify config)
uv run --env-file .env python -m src.manager "https://github.com/example/repo" \
  --type security \
  --scenario "ab-test-experiment"
```

## Filtering in Langfuse UI

With scenario tracking, you can easily filter traces in the Langfuse UI:

### By Scenario Tag
Filter by tag: `scenario:security-vulnerabilities-detection`

### By Trace Name
Search for traces containing: `[security-vulnerabilities-detection]`

### By Metadata
Query metadata field: `scenario = "security-vulnerabilities-detection"`

### By Session
Filter by session ID to see all related analyses

## Benefits

### 1. Clear Identification
Immediately identify which agent and scenario is running from the trace name.

### 2. Easy Filtering
Filter traces by scenario, agent, or analysis type using tags.

### 3. Better Organization
Group related test runs using session IDs and scenarios.

### 4. Improved Debugging
Quickly find traces for specific scenarios when debugging issues.

### 5. Evaluation Tracking
Track performance across different test scenarios systematically.

### 6. Cost Analysis
Calculate costs per scenario or evaluation campaign.

## Example Output

When running with scenario tracking, you'll see:

```
Starting security analysis for: https://github.com/openai/openai-python
Scenario: security-vulnerabilities-detection
✓ Langfuse tracing enabled: static-code-analysis-agent: security analysis [security-vulnerabilities-detection] - openai/openai-python

[... analysis runs ...]

✓ Trace updated with enhanced observability:
  - Name: static-code-analysis-agent: security analysis [security-vulnerabilities-detection] - openai/openai-python
  - User: test-user-123
  - Session: demo-session-001
  - Scenario: security-vulnerabilities-detection
  - Tags: static-analysis, security, langgraph, production, scenario:security-vulnerabilities-detection, success, has-critical-issues, has-high-issues
  - Version: vgpt-4-turbo-preview_0.3
```

## Backward Compatibility

The `scenario_name` parameter is optional:
- **Without scenario**: Trace name omits the scenario part
- **With scenario**: Trace name includes `[scenario_name]`
- **Default behavior**: Works exactly as before if scenario is not provided

## Integration with Evaluation Frameworks

This feature is designed to work well with evaluation frameworks:

```python
# Example: Running evaluations with scenario tracking
evaluation_scenarios = [
    "security-vulnerabilities",
    "code-quality-issues",
    "dependency-vulnerabilities",
    "performance-bottlenecks"
]

for scenario in evaluation_scenarios:
    result = await manager.analyze_repository(
        repository_url=test_repo_url,
        analysis_type="security",
        session_id="evaluation-run-2024-01",
        scenario_name=scenario
    )
    # Store results for comparison
```

## Best Practices

### 1. Consistent Naming
Use consistent scenario names across runs:
- ✅ Good: `security-vulnerabilities-detection`
- ❌ Bad: `sec-vuln-detect`, `security_check`, `sec-test`

### 2. Descriptive Names
Make scenario names self-explanatory:
- ✅ Good: `pre-release-security-audit`
- ❌ Bad: `test1`, `scenario-a`

### 3. Use Kebab-Case
Use kebab-case for scenario names:
- ✅ Good: `security-vulnerabilities-detection`
- ❌ Bad: `SecurityVulnerabilitiesDetection`, `security_vulnerabilities_detection`

### 4. Group Related Scenarios
Use session IDs to group related scenario runs:
```bash
SESSION_ID="security-audit-$(date +%Y%m%d)"
```

### 5. Document Scenarios
Keep a list of standard scenarios for your team:
```
# Standard Security Scenarios
- security-vulnerabilities-detection
- pre-release-security-audit
- post-deployment-security-check

# Standard Quality Scenarios
- code-style-compliance
- complexity-analysis
- documentation-coverage
```

## Troubleshooting

### Scenario Not Showing in Trace Name

**Problem**: The scenario is not appearing in the trace name.

**Solution**: Ensure you're passing `--scenario` or `scenario_name` parameter:
```bash
# ❌ Missing scenario
python -m src.manager "https://github.com/example/repo" --type security

# ✅ With scenario
python -m src.manager "https://github.com/example/repo" --type security --scenario "my-scenario"
```

### Scenario Tag Not Appearing

**Problem**: The scenario tag is not in the tags list.

**Solution**: This should only happen if `scenario_name` is None or empty. Verify you're passing the parameter correctly.

### Multiple Scenarios in Same Session

**Problem**: How to track multiple scenarios in the same session?

**Solution**: Use the same session ID with different scenario names:
```bash
SESSION_ID="my-session"

# Scenario 1
python -m src.manager ... --session-id "$SESSION_ID" --scenario "scenario-1"

# Scenario 2
python -m src.manager ... --session-id "$SESSION_ID" --scenario "scenario-2"
```

Then filter by session ID in Langfuse to see all scenarios together.

## Summary

The trace naming and scenario tracking feature provides:

- ✅ **Descriptive trace names** that identify the agent, analysis type, scenario, and repository
- ✅ **Scenario tags** for easy filtering
- ✅ **Metadata tracking** for comprehensive scenario information
- ✅ **Backward compatibility** with optional scenario parameter
- ✅ **Better organization** of test runs and evaluations
- ✅ **Improved debugging** with clear trace identification

This makes it easy to track, filter, and analyze traces from specific scenarios, evaluation campaigns, or test runs in production.
