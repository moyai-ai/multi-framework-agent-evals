"""Public API for the Google ADK agent Deepeval runner."""

from __future__ import annotations

from typing import Any

__all__ = ["run_deepeval_for_file", "run_deepeval_sync"]


def run_deepeval_for_file(*args: Any, **kwargs: Any):
    from google_adk_deepeval_run.evaluators.deepeval_runner import run_deepeval_for_file

    return run_deepeval_for_file(*args, **kwargs)


def run_deepeval_sync(*args: Any, **kwargs: Any):
    from google_adk_deepeval_run.evaluators.deepeval_runner import run_deepeval_sync

    return run_deepeval_sync(*args, **kwargs)
