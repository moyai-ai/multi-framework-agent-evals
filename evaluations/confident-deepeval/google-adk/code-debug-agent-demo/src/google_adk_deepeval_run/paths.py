"""Shared path helpers for the Google ADK agent evaluation project."""

from __future__ import annotations

from pathlib import Path
import sys


def _resolve_workspace_root() -> Path:
    return Path(__file__).resolve().parents[6]


WORKSPACE_ROOT = _resolve_workspace_root()
AGENT_DEMO_ROOT = WORKSPACE_ROOT / "frameworks" / "google-adk" / "code-debug-agent-demo"
AGENT_SRC_ROOT = AGENT_DEMO_ROOT / "src"
DEFAULT_SCENARIO_DIR = AGENT_SRC_ROOT / "scenarios"
DEFAULT_REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


def ensure_agent_src_on_path() -> None:
    """Make sure the google-adk agent source directory is importable."""
    if not AGENT_SRC_ROOT.exists():
        raise FileNotFoundError(
            f"Agent source directory not found at {AGENT_SRC_ROOT}. "
            "Verify the google-adk code-debug-agent-demo project is available."
        )

    for path in (AGENT_DEMO_ROOT, AGENT_SRC_ROOT):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
