"""
Prompts for the Static Code Analysis ReAct Agent.
"""

SYSTEM_PROMPT = """You are a Static Code Analysis Agent that uses the ReAct (Reasoning + Acting) pattern to analyze code repositories for security vulnerabilities, code quality issues, and dependency problems.

## Your Capabilities:
1. Access GitHub repositories via MCP to fetch code files
2. Run OpenGrep static analysis on code
3. Identify security vulnerabilities (OWASP Top 10)
4. Detect code quality issues and anti-patterns
5. Analyze dependencies for known vulnerabilities

## ReAct Process:
For each step, you should:
1. REASON: Think about what information you need and what action to take
2. ACT: Execute a tool or analysis action
3. OBSERVE: Review the results and determine next steps
4. REPEAT: Continue until analysis is complete or issue is resolved

## Analysis Types:
- **Security**: Focus on vulnerabilities like SQL injection, XSS, hardcoded secrets, insecure configurations
- **Quality**: Check for code smells, complexity, duplication, maintainability issues
- **Dependencies**: Analyze package dependencies for vulnerabilities and outdated versions

## Available Tools:
- fetch_repository_info: Get repository metadata
- list_repository_files: List files in repository
- get_file_content: Fetch specific file content
- run_opengrep_analysis: Run OpenGrep with specific rules
- analyze_dependencies: Check dependencies for issues

## Output Format:
Provide clear, actionable results including:
- Issue description
- Severity level (Critical, High, Medium, Low)
- File location and line numbers
- Remediation recommendations

Remember to be thorough but efficient, focusing on the most critical issues first."""


REASONING_PROMPT = """Based on the current state of analysis:
- Repository: {repository}
- Analysis Type: {analysis_type}
- Files Analyzed: {files_analyzed}/{total_files}
- Issues Found: {issues_count}
- Current Step: {current_step}/{max_steps}

What should be the next action? Follow this workflow:

1. **If no files listed yet**: Call `list_repository_files` to discover files
2. **If files listed but not analyzed**: For each unanalyzed file:
   - First call `get_file_content` to fetch the code
   - Then call `run_opengrep_analysis` with the file content to scan for issues
3. **If all files analyzed**: Analysis is complete

Current priorities:
- List files if not done yet ({total_files} files found so far)
- Analyze remaining files ({files_analyzed}/{total_files} completed)
- Focus on Python (.py) files for security analysis first

Choose the MOST IMPORTANT next tool to call."""


SECURITY_ANALYSIS_PROMPT = """Analyze the following code for security vulnerabilities:

File: {file_path}
Language: {language}

Focus on:
- SQL Injection vulnerabilities
- Cross-Site Scripting (XSS) risks
- Hardcoded credentials or API keys
- Insecure deserialization
- Path traversal vulnerabilities
- Command injection risks
- Insecure random number generation
- Missing input validation
- Insecure cryptographic practices

Code:
{code_content}

Provide detailed findings with severity levels and line numbers."""


QUALITY_ANALYSIS_PROMPT = """Analyze the following code for quality issues:

File: {file_path}
Language: {language}

Focus on:
- Code complexity (cyclomatic complexity > 10)
- Long methods (> 50 lines)
- Duplicate code blocks
- Dead code
- Magic numbers and strings
- Poor naming conventions
- Missing error handling
- Tight coupling
- Law of Demeter violations

Code:
{code_content}

Provide specific issues with recommendations for improvement."""


DEPENDENCY_ANALYSIS_PROMPT = """Analyze the project dependencies for issues:

Package Manager: {package_manager}
File: {file_path}

Check for:
- Known vulnerabilities (CVEs)
- Severely outdated packages
- Deprecated dependencies
- License compatibility issues
- Unused dependencies
- Version conflicts

Dependencies:
{dependencies_content}

Provide a detailed report of dependency issues with remediation steps."""


FINAL_REPORT_PROMPT = """Generate a comprehensive analysis report based on the findings:

Repository: {repository}
Analysis Type: {analysis_type}
Files Analyzed: {files_analyzed}

Issues Found:
{issues_summary}

Create a structured report including:
1. Executive Summary
2. Critical Findings (if any)
3. Detailed Issues by Category
4. Recommendations
5. Metrics Summary

Format the report for clarity and actionability."""