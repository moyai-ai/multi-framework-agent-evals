"""Helpers for discovering and preparing scenario files for evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from google_adk_deepeval_run.paths import (
    AGENT_DEMO_ROOT,
    DEFAULT_SCENARIO_DIR,
    ensure_agent_src_on_path,
)


ensure_agent_src_on_path()

from runner import ScenarioRunner, Scenario, ConversationTurn  # type: ignore  # noqa: E402


@dataclass
class ScenarioFile:
    path: Path
    scenario_count: int


@dataclass
class TurnExpectations:
    expected_tools: List[str]
    expected_keywords: List[str]
    expected_links: List[str]


def list_scenario_files(directory: Path | None = None, glob: str = "*.json") -> List[ScenarioFile]:
    root = directory or DEFAULT_SCENARIO_DIR
    files = sorted(root.glob(glob))
    results: List[ScenarioFile] = []

    for path in files:
        try:
            scenarios = ScenarioRunner.load_scenarios(str(path))
            results.append(ScenarioFile(path=path, scenario_count=len(scenarios)))
        except FileNotFoundError:
            continue

    return results


def load_scenarios_from_file(path: Path) -> Sequence[Scenario]:
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")
    return ScenarioRunner.load_scenarios(str(path))


def collect_turn_expectations(turns: Iterable[ConversationTurn]) -> TurnExpectations:
    tools: List[str] = []
    keywords: List[str] = []
    links: List[str] = []

    for turn in turns:
        if turn.expected_tools:
            tools.extend(turn.expected_tools)
        if turn.expected_keywords:
            keywords.extend(turn.expected_keywords)
        if turn.expected_links:
            links.extend(turn.expected_links)

    return TurnExpectations(
        expected_tools=sorted(set(tools)),
        expected_keywords=sorted(set(keywords)),
        expected_links=sorted(set(links)),
    )


__all__ = [
    "ScenarioFile",
    "TurnExpectations",
    "list_scenario_files",
    "load_scenarios_from_file",
    "collect_turn_expectations",
    "Scenario",
    "ConversationTurn",
]
