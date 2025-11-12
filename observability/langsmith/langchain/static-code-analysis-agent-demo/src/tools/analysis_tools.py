"""
Analysis tools for processing and summarizing code analysis results.
"""

import json
from typing import Dict, Any, List, Optional
from collections import defaultdict
from langchain_core.tools import tool


@tool
async def summarize_findings(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Summarize analysis findings by category and severity.

    Args:
        issues: List of identified issues

    Returns:
        Summary of findings with statistics and categorization
    """
    if not issues:
        return {
            "total_issues": 0,
            "summary": "No issues found",
            "categories": {},
            "severities": {},
            "files_affected": []
        }

    # Group by category
    categories = defaultdict(list)
    severities = defaultdict(int)
    files_affected = set()

    for issue in issues:
        category = issue.get("category", issue.get("rule_id", "unknown"))
        severity = issue.get("severity", "INFO")
        file_path = issue.get("file_path", "unknown")

        categories[category].append(issue)
        severities[severity] += 1
        files_affected.add(file_path)

    # Create summary
    summary = {
        "total_issues": len(issues),
        "critical_issues": severities.get("CRITICAL", 0),
        "high_issues": severities.get("HIGH", 0) + severities.get("ERROR", 0),
        "medium_issues": severities.get("MEDIUM", 0) + severities.get("WARNING", 0),
        "low_issues": severities.get("LOW", 0),
        "info_issues": severities.get("INFO", 0),
        "categories": {k: len(v) for k, v in categories.items()},
        "files_affected": list(files_affected),
        "top_issues": _get_top_issues(categories)
    }

    return summary


@tool
async def generate_remediation_plan(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a remediation plan for identified issues.

    Args:
        issues: List of identified issues

    Returns:
        Prioritized remediation plan
    """
    if not issues:
        return {
            "plan": [],
            "estimated_effort": "No remediation needed"
        }

    # Sort issues by severity
    severity_order = {"CRITICAL": 0, "HIGH": 1, "ERROR": 1, "MEDIUM": 2, "WARNING": 2, "LOW": 3, "INFO": 4}
    sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.get("severity", "INFO"), 4))

    plan = []
    for issue in sorted_issues[:10]:  # Top 10 most critical issues
        remediation = _get_remediation_for_issue(issue)
        plan.append({
            "issue": issue.get("message", issue.get("description", "Unknown issue")),
            "severity": issue.get("severity", "INFO"),
            "file": issue.get("file_path", "unknown"),
            "line": issue.get("line", 0),
            "remediation": remediation,
            "effort": _estimate_effort(issue)
        })

    total_effort = sum(
        {"low": 1, "medium": 3, "high": 8}.get(_estimate_effort(issue), 1)
        for issue in sorted_issues
    )

    return {
        "plan": plan,
        "total_issues": len(issues),
        "estimated_effort_hours": total_effort,
        "priority_issues": len([i for i in issues if i.get("severity") in ["CRITICAL", "HIGH", "ERROR"]])
    }


@tool
async def analyze_code_complexity(code_content: str, file_path: str) -> Dict[str, Any]:
    """
    Analyze code complexity metrics.

    Args:
        code_content: The code to analyze
        file_path: Path of the file being analyzed

    Returns:
        Complexity metrics and recommendations
    """
    lines = code_content.split('\n')

    # Basic complexity analysis
    metrics = {
        "total_lines": len(lines),
        "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
        "comment_lines": len([l for l in lines if l.strip().startswith('#')]),
        "blank_lines": len([l for l in lines if not l.strip()]),
        "functions": _count_functions(code_content),
        "classes": _count_classes(code_content),
        "complexity_issues": []
    }

    # Check for long functions
    function_lengths = _get_function_lengths(code_content)
    for func_name, length in function_lengths.items():
        if length > 50:
            metrics["complexity_issues"].append({
                "type": "long_function",
                "function": func_name,
                "lines": length,
                "recommendation": f"Consider refactoring {func_name} - functions should be under 50 lines"
            })

    # Check for deep nesting
    max_nesting = _get_max_nesting(code_content)
    if max_nesting > 4:
        metrics["complexity_issues"].append({
            "type": "deep_nesting",
            "level": max_nesting,
            "recommendation": "Reduce nesting levels - consider extracting nested logic into separate functions"
        })

    metrics["complexity_score"] = _calculate_complexity_score(metrics)
    metrics["file_path"] = file_path

    return metrics


@tool
async def analyze_dependencies(requirements_content: str, file_path: str = "requirements.txt") -> Dict[str, Any]:
    """
    Analyze project dependencies for known vulnerabilities.

    Args:
        requirements_content: Content of the requirements file
        file_path: Path of the requirements file being analyzed

    Returns:
        Dependency analysis results with vulnerabilities
    """
    dependencies = []
    vulnerabilities = []

    # Parse requirements
    lines = requirements_content.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Simple parsing - in real implementation, use proper parser
            if '==' in line:
                package, version = line.split('==', 1)
                dependencies.append({
                    "package": package.strip(),
                    "version": version.strip(),
                    "type": "pinned"
                })
            elif '>=' in line:
                package = line.split('>=', 1)[0]
                dependencies.append({
                    "package": package.strip(),
                    "version": ">=",
                    "type": "minimum"
                })
            else:
                dependencies.append({
                    "package": line,
                    "version": "unspecified",
                    "type": "unpinned"
                })

    # Check for unpinned dependencies (security issue)
    for dep in dependencies:
        if dep["type"] == "unpinned":
            vulnerabilities.append({
                "package": dep["package"],
                "severity": "MEDIUM",
                "type": "unpinned-dependency",
                "message": f"Dependency '{dep['package']}' is not pinned to a specific version",
                "recommendation": "Pin dependencies to specific versions for reproducible builds"
            })

    return {
        "file_path": file_path,
        "total_dependencies": len(dependencies),
        "dependencies": dependencies,
        "vulnerabilities": vulnerabilities,
        "vulnerable_count": len(vulnerabilities)
    }


@tool
async def compare_analysis_results(
    previous_results: List[Dict[str, Any]],
    current_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compare two sets of analysis results to track improvements or regressions.

    Args:
        previous_results: Previous analysis results
        current_results: Current analysis results

    Returns:
        Comparison showing improvements and regressions
    """
    prev_issues = {f"{i.get('file_path')}:{i.get('line')}:{i.get('rule_id')}" for i in previous_results}
    curr_issues = {f"{i.get('file_path')}:{i.get('line')}:{i.get('rule_id')}" for i in current_results}

    fixed = prev_issues - curr_issues
    new = curr_issues - prev_issues
    unchanged = prev_issues & curr_issues

    # Calculate severity changes
    prev_severity = _count_by_severity(previous_results)
    curr_severity = _count_by_severity(current_results)

    return {
        "summary": {
            "previous_total": len(previous_results),
            "current_total": len(current_results),
            "fixed": len(fixed),
            "new": len(new),
            "unchanged": len(unchanged)
        },
        "severity_changes": {
            "critical": curr_severity["CRITICAL"] - prev_severity["CRITICAL"],
            "high": curr_severity["HIGH"] - prev_severity["HIGH"],
            "medium": curr_severity["MEDIUM"] - prev_severity["MEDIUM"],
            "low": curr_severity["LOW"] - prev_severity["LOW"]
        },
        "improvement_score": _calculate_improvement_score(previous_results, current_results)
    }


# Helper functions

def _get_top_issues(categories: Dict[str, List]) -> List[Dict[str, Any]]:
    """Get top issues by category."""
    top_issues = []
    for category, issues in categories.items():
        if issues:
            # Get the most severe issue from this category
            sorted_issues = sorted(
                issues,
                key=lambda x: {"CRITICAL": 0, "HIGH": 1, "ERROR": 1, "MEDIUM": 2, "WARNING": 2, "LOW": 3, "INFO": 4}.get(
                    x.get("severity", "INFO"), 4
                )
            )
            if sorted_issues:
                top_issues.append({
                    "category": category,
                    "count": len(issues),
                    "most_severe": sorted_issues[0]
                })

    return sorted(top_issues, key=lambda x: x["count"], reverse=True)[:5]


def _get_remediation_for_issue(issue: Dict[str, Any]) -> str:
    """Get remediation advice for a specific issue."""
    rule_id = issue.get("rule_id", "")

    remediations = {
        "sql-injection": "Use parameterized queries or prepared statements instead of string concatenation",
        "hardcoded-secret": "Move secrets to environment variables or secure secret management system",
        "xss-vulnerability": "Sanitize user input and use proper output encoding",
        "command-injection": "Validate and sanitize input, use subprocess with list arguments instead of shell=True",
        "empty-exception-handler": "Log exceptions and handle them appropriately",
        "todo-comment": "Complete the implementation or create a tracking ticket"
    }

    if rule_id in remediations:
        return remediations[rule_id]

    # For dependency vulnerabilities
    if "cve" in issue:
        return issue.get("recommendation", "Update to the latest secure version")

    return "Review and fix according to security best practices"


def _estimate_effort(issue: Dict[str, Any]) -> str:
    """Estimate remediation effort for an issue."""
    severity = issue.get("severity", "INFO")

    if severity in ["CRITICAL", "HIGH", "ERROR"]:
        return "high"
    elif severity in ["MEDIUM", "WARNING"]:
        return "medium"
    else:
        return "low"


def _count_functions(code_content: str) -> int:
    """Count number of functions in code."""
    return code_content.count("def ") + code_content.count("function ") + code_content.count("func ")


def _count_classes(code_content: str) -> int:
    """Count number of classes in code."""
    return code_content.count("class ")


def _get_function_lengths(code_content: str) -> Dict[str, int]:
    """Get the length of each function."""
    function_lengths = {}
    lines = code_content.split('\n')

    current_function = None
    current_length = 0
    indent_level = 0

    for line in lines:
        if "def " in line:
            if current_function:
                function_lengths[current_function] = current_length
            current_function = line.split("def ")[1].split("(")[0] if "def " in line else None
            current_length = 1
            indent_level = len(line) - len(line.lstrip())
        elif current_function:
            if line.strip() and (len(line) - len(line.lstrip())) > indent_level:
                current_length += 1
            elif line.strip() and (len(line) - len(line.lstrip())) <= indent_level:
                function_lengths[current_function] = current_length
                current_function = None

    if current_function:
        function_lengths[current_function] = current_length

    return function_lengths


def _get_max_nesting(code_content: str) -> int:
    """Get maximum nesting level in code."""
    lines = code_content.split('\n')
    max_nesting = 0

    for line in lines:
        if line.strip():
            # Simple heuristic: count indentation
            nesting = (len(line) - len(line.lstrip())) // 4
            max_nesting = max(max_nesting, nesting)

    return max_nesting


def _calculate_complexity_score(metrics: Dict[str, Any]) -> str:
    """Calculate overall complexity score."""
    score = 0

    # Penalize for long file
    if metrics["code_lines"] > 500:
        score += 3
    elif metrics["code_lines"] > 200:
        score += 1

    # Penalize for low comment ratio
    if metrics["code_lines"] > 0:
        comment_ratio = metrics["comment_lines"] / metrics["code_lines"]
        if comment_ratio < 0.1:
            score += 2

    # Penalize for complexity issues
    score += len(metrics["complexity_issues"])

    if score <= 2:
        return "low"
    elif score <= 5:
        return "medium"
    else:
        return "high"


def _count_by_severity(issues: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count issues by severity."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for issue in issues:
        severity = issue.get("severity", "INFO")
        if severity == "ERROR":
            severity = "HIGH"
        elif severity == "WARNING":
            severity = "MEDIUM"
        if severity in counts:
            counts[severity] += 1
    return counts


def _calculate_improvement_score(previous: List, current: List) -> float:
    """Calculate improvement score between two result sets."""
    if not previous:
        return 0.0

    # Weight by severity
    weights = {"CRITICAL": 10, "HIGH": 5, "ERROR": 5, "MEDIUM": 2, "WARNING": 2, "LOW": 1, "INFO": 0.5}

    prev_score = sum(weights.get(i.get("severity", "INFO"), 0.5) for i in previous)
    curr_score = sum(weights.get(i.get("severity", "INFO"), 0.5) for i in current)

    if prev_score == 0:
        return 0.0

    improvement = (prev_score - curr_score) / prev_score * 100
    return round(improvement, 2)