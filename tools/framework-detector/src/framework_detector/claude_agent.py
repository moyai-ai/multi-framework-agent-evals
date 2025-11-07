"""
Claude Agent SDK implementation for detecting AI frameworks in codebases.

This module uses the Claude Agent SDK to analyze a codebase and identify
which AI agent frameworks have been used.
"""

import argparse
import asyncio
import json
import os
from datetime import datetime
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)


def get_initial_cwd(path: str | None = None) -> str:
    """
    Get the initial working directory for the agent.
    
    If a path is provided, use that. Otherwise, start from the current
    working directory and let the agent discover the repo root using Bash.

    Args:
        path: Optional path to the codebase. If not provided, defaults to
              the current working directory.

    Returns:
        Absolute path string pointing to the initial working directory.
    """
    if path:
        return os.path.abspath(os.path.expanduser(path))
    return os.path.abspath(os.getcwd())


def create_report_dir() -> str:
    """Create reports directory if it doesn't exist."""
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up 2 levels: framework_detector -> src -> framework-detector
    # Then create reports directory within framework-detector
    reports_dir = os.path.join(script_dir, "..", "..", "reports")
    reports_dir = os.path.abspath(reports_dir)
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


async def run_framework_detection(path: str | None = None) -> dict[str, Any]:
    """
    Run the Claude agent to detect frameworks in the codebase.

    Args:
        path: Optional path to the codebase to analyze. If not provided,
              the agent will discover the git repository root using Bash.

    Returns:
        Dictionary containing the detection results and metadata.
    """
    # Get the initial working directory
    initial_cwd = get_initial_cwd(path)

    # Configure the agent with allowed tools
    # Bash is restricted to only git rev-parse commands using fine-grained permissions
    # Format: Bash(git rev-parse:*) matches any command starting with "git rev-parse"
    options = ClaudeAgentOptions(
        allowed_tools=["TodoWrite", "Read", "Grep", "Glob", "Bash(git rev-parse:*)"],
        cwd=initial_cwd,  # Start from initial directory or current working directory
    )

    # The prompt for framework detection
    # If no path is provided, instruct the agent to first find the repo root
    if path:
        prompt = "Which agent framework has been used for building agents in this code base"
    else:
        prompt = """First, use the Bash tool to find the git repository root by running 'git rev-parse --show-toplevel'. 
Then, analyze the codebase starting from that root directory to determine which agent framework has been used for building agents in this codebase."""

    print(f"Starting Claude Agent SDK framework detection...")
    print(f"Initial working directory: {initial_cwd}")
    if not path:
        print("Agent will discover the git repository root using Bash (restricted to 'git rev-parse' commands)")
    print(f"Using tools: TodoWrite, Read, Grep, Glob, Bash(git rev-parse:*)\n")

    # Collect all messages and responses
    messages = []
    text_responses = []
    tools_used = []

    # Query the agent
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            print(f"\n[Agent Response]")

            # Process content blocks
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"{block.text}")
                    text_responses.append(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"[Using tool: {block.name}]")
                    tools_used.append(block.name)

            # Store the message
            messages.append({
                "type": "assistant",
                "content": [
                    {
                        "type": "text" if isinstance(b, TextBlock) else "tool_use",
                        "text": b.text if isinstance(b, TextBlock) else None,
                        "name": b.name if isinstance(b, ToolUseBlock) else None,
                    }
                    for b in message.content
                ],
            })

        elif isinstance(message, ResultMessage):
            print(f"\n[Execution Complete]")
            print(f"Token usage: {message.usage}")

            # Store result metadata
            result_data = {
                "type": "result",
                "usage": message.usage,
            }
            messages.append(result_data)

    # Compile the report
    report = {
        "prompt": prompt,
        "initial_cwd": initial_cwd,
        "timestamp": datetime.now().isoformat(),
        "tools_allowed": ["TodoWrite", "Read", "Grep", "Glob", "Bash(git rev-parse:*)"],
        "tools_used": list(set(tools_used)),
        "messages": messages,
        "summary": "\n\n".join(text_responses),
    }

    return report


def save_report(report: dict[str, Any], output_format: str = "json") -> str:
    """
    Save the detection report to a file.

    Args:
        report: The report data to save
        output_format: Format to save the report in ('json' or 'md')

    Returns:
        Path string to the saved report file
    """
    reports_dir = create_report_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if output_format == "json":
        report_path = os.path.join(reports_dir, f"framework_detection_{timestamp}.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
    else:  # markdown
        report_path = os.path.join(reports_dir, f"framework_detection_{timestamp}.md")
        with open(report_path, "w") as f:
            f.write("# Framework Detection Report\n\n")
            f.write(f"**Timestamp:** {report['timestamp']}\n\n")
            f.write(f"**Initial Working Directory:** {report.get('initial_cwd', report.get('codebase_root', 'N/A'))}\n\n")
            f.write(f"**Prompt:** {report['prompt']}\n\n")
            f.write(f"**Tools Used:** {', '.join(report['tools_used'])}\n\n")
            f.write("## Summary\n\n")
            f.write(report['summary'])
            f.write("\n\n")

            # Add usage info if available
            for msg in report['messages']:
                if msg.get('type') == 'result' and msg.get('usage'):
                    f.write("## Usage Statistics\n\n")
                    f.write(f"```json\n{json.dumps(msg['usage'], indent=2)}\n```\n")

    return report_path


async def main(path: str | None = None):
    """
    Main entry point for the framework detector agent.

    Args:
        path: Optional path to the codebase to analyze. If not provided,
              defaults to the repository root.
    """
    try:
        # Run the detection
        report = await run_framework_detection(path)

        # Save reports in both formats
        json_path = save_report(report, output_format="json")
        md_path = save_report(report, output_format="md")

        print(f"\n{'='*60}")
        print(f"Reports generated:")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"Error running framework detection: {e}")
        raise


def cli_entry():
    """CLI entry point for UV script."""
    parser = argparse.ArgumentParser(
        description="Detect AI agent frameworks in a codebase using Claude Agent SDK"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Path to the codebase to analyze (defaults to repository root)",
    )
    parser.add_argument(
        "-p",
        "--path",
        dest="path_flag",
        default=None,
        help="Path to the codebase to analyze (alternative flag syntax)",
    )

    args = parser.parse_args()

    # Use either positional argument or flag (flag takes precedence)
    path = args.path_flag or args.path

    asyncio.run(main(path))


if __name__ == "__main__":
    cli_entry()
