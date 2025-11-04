"""Pytest configuration and fixtures for Claude Agent SDK tests."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from claude_agent_sdk._errors import CLINotFoundError, ProcessError


def _find_claude_cli() -> str | None:
    """Find Claude Code CLI binary."""
    # Check PATH first
    if cli := shutil.which("claude"):
        return cli
    
    # Check common installation locations
    locations = [
        Path.home() / ".npm-global/bin/claude",
        Path("/usr/local/bin/claude"),
        Path.home() / ".local/bin/claude",
        Path.home() / "node_modules/.bin/claude",
        Path.home() / ".yarn/bin/claude",
    ]
    
    for path in locations:
        if path.exists() and path.is_file():
            return str(path)
    
    return None


def _install_claude_cli() -> bool:
    """Attempt to install Claude CLI via npm."""
    # Check if npm is available
    if not shutil.which("npm"):
        print("npm not found. Cannot install Claude CLI automatically.", file=sys.stderr)
        return False
    
    try:
        print("Installing Claude CLI...", file=sys.stderr)
        result = subprocess.run(
            ["npm", "install", "-g", "@anthropic-ai/claude-code"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("Claude CLI installed successfully.", file=sys.stderr)
            return True
        else:
            print(f"Failed to install Claude CLI: {result.stderr}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("Installation timed out.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error installing Claude CLI: {e}", file=sys.stderr)
        return False


@pytest.fixture(scope="session", autouse=True)
def check_claude_cli():
    """Check if Claude CLI is available, install if needed."""
    cli_path = _find_claude_cli()
    if not cli_path:
        # Try to install it
        if _install_claude_cli():
            # Check again after installation
            cli_path = _find_claude_cli()
        
        if not cli_path:
            pytest.skip(
                "Claude Code CLI not found. To install:\n"
                "  npm install -g @anthropic-ai/claude-code\n"
                "\nIf already installed locally, try:\n"
                '  export PATH="$HOME/node_modules/.bin:$PATH"\n'
                "\nOr provide the path via ClaudeAgentOptions:\n"
                "  ClaudeAgentOptions(cli_path='/path/to/claude')"
            )


@pytest.fixture
def skip_if_cli_unavailable():
    """Helper to skip tests if CLI is unavailable or misconfigured."""
    def _skip_if_error(error: Exception):
        """Check if error is CLI-related and skip test with helpful message."""
        if isinstance(error, CLINotFoundError):
            pytest.skip(
                "Claude Code CLI not found. Install with:\n"
                "  npm install -g @anthropic-ai/claude-code\n"
                "\nIf already installed locally, try:\n"
                '  export PATH="$HOME/node_modules/.bin:$PATH"'
            )
        elif isinstance(error, ProcessError):
            pytest.skip(
                f"Claude Code CLI failed: {error}\n"
                "This may be due to:\n"
                "  - Missing or invalid ANTHROPIC_API_KEY\n"
                "  - CLI not properly installed\n"
                "  - Network connectivity issues\n"
                "\nTo fix, ensure ANTHROPIC_API_KEY is set correctly."
            )
        elif isinstance(error, Exception) and "Command failed" in str(error):
            pytest.skip(
                f"Claude Code CLI command failed: {error}\n"
                "Check that:\n"
                "  - ANTHROPIC_API_KEY is set correctly\n"
                "  - CLI is properly installed: npm install -g @anthropic-ai/claude-code"
            )
        # Re-raise if not a CLI error
        raise error
    return _skip_if_error


@pytest.fixture(scope="session", autouse=True)
def load_environment():
    """Load environment variables from environment (no .env file required)."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        # Use mock API key for unit tests
        os.environ["ANTHROPIC_API_KEY"] = "test_api_key_12345"


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def scenarios():
    """Load test scenarios from JSON file."""
    scenarios_file = Path(__file__).parent.parent / "src" / "scenarios" / "quick_start_scenarios.json"
    with open(scenarios_file, "r") as f:
        data = json.load(f)
    return data["scenarios"]


@pytest.fixture
def scenario_by_name(scenarios):
    """Get a specific scenario by name."""
    def _get_scenario(name: str) -> Dict[str, Any]:
        for scenario in scenarios:
            if scenario["name"] == name:
                return scenario
        raise ValueError(f"Scenario '{name}' not found")
    return _get_scenario


@pytest.fixture
def mock_api_key(monkeypatch):
    """Set a mock API key for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_api_key_12345")
