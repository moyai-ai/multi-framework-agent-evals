# Framework Detector

A tool for detecting AI agent frameworks and analyzing codebases using the Claude Agent SDK.

## Features

- **Claude Agent SDK Integration**: Uses Claude Agent SDK to analyze codebases intelligently
- **Built-in Tools**: Leverages TodoWrite, Read, Grep, Glob, and Bash (restricted to git rev-parse) for comprehensive codebase analysis
- **Report Generation**: Creates both JSON and Markdown reports with detailed findings
- **Easy Execution**: Run with simple UV commands

## Installation

Install dependencies using UV:

```bash
unset VIRTUAL_ENV && uv sync
```

## Usage

### Running the Claude Agent

The Claude agent analyzes your codebase to identify which agent frameworks have been used:

```bash
unset VIRTUAL_ENV && uv run framework-agent

# Using --path flag
unset VIRTUAL_ENV && uv run framework-agent /path/to/your/codebase
```

This will:
1. Discover the git repository root using Bash (restricted to `git rev-parse` commands)
2. Analyze the codebase starting from the repository root
3. Use Claude Agent SDK with TodoWrite, Read, Grep, Glob, and Bash tools
4. Generate detailed reports in the `reports/` directory

### Output

The agent generates two report files:

- `reports/framework_detection_YYYYMMDD_HHMMSS.json` - Structured JSON report with complete data
- `reports/framework_detection_YYYYMMDD_HHMMSS.md` - Human-readable Markdown summary

### Example Output

```
Starting Claude Agent SDK framework detection...
Initial working directory: /path/to/codebase
Agent will discover the git repository root using Bash (restricted to 'git rev-parse' commands)
Using tools: TodoWrite, Read, Grep, Glob, Bash(git rev-parse:*)

[Agent Response]
I'll search through the codebase to identify which agent framework has been used.
...

============================================================
Reports generated:
  JSON: reports/framework_detection_20251105_145148.json
  Markdown: reports/framework_detection_20251105_145148.md
============================================================
```

## Configuration

The agent is configured with:

- **Prompt**: "Which agent framework has been used for building agents in this code base"
- **Allowed Tools**: TodoWrite, Read, Grep, Glob, Bash(git rev-parse:*)
- **Bash Restriction**: Bash tool is restricted to only `git rev-parse` commands for security
- **Working Directory**: Automatically discovers git repository root using `git rev-parse --show-toplevel`, or uses provided path

## Environment Variables

Ensure your `.env` file contains:

```
ANTHROPIC_API_KEY=your_api_key_here
```

## Development

### Project Structure

```
framework-detector/
├── src/framework_detector/
│   ├── claude_agent.py      # Claude Agent SDK implementation
│   └── main.py              # Original framework detector
├── reports/                  # Generated reports
├── pyproject.toml           # Dependencies and scripts
├── .env                     # API keys
└── README.md                # This file
```

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black src/
uv run ruff check src/
```

## How It Works

1. **Initialization**: Sets up the Claude Agent SDK with allowed tools
2. **Analysis**: The agent autonomously explores the codebase using Read, Grep, and Glob
3. **Reporting**: Collects all responses, tool usage, and token statistics
4. **Output**: Generates comprehensive reports in both JSON and Markdown formats

## Tools Used by the Agent

- **TodoWrite**: Task management and planning during analysis
- **Read**: Reading file contents
- **Grep**: Searching for patterns in code
- **Glob**: Finding files by pattern matching
- **Bash**: Restricted to `git rev-parse` commands only for discovering repository root

