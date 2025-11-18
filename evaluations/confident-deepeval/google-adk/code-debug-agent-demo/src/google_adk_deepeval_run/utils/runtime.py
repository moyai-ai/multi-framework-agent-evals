"""Runtime helpers for bootstrapping the evaluation environment."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv

from google_adk_deepeval_run.paths import AGENT_DEMO_ROOT, ensure_agent_src_on_path


def load_env_files(extra_paths: Optional[Iterable[Path]] = None) -> None:
    """Load .env files so the agent can authenticate with Gemini/StackExchange."""
    ensure_agent_src_on_path()

    candidate_paths = [
        AGENT_DEMO_ROOT / ".env",
        AGENT_DEMO_ROOT / ".env.example",
    ]

    if extra_paths:
        candidate_paths.extend(extra_paths)

    for env_path in candidate_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)
