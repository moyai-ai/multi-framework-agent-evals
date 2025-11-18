"""Async runner that executes scenario files and scores them with Deepeval metrics."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from deepeval.test_case import LLMTestCase
from deepeval import evaluate

from google_adk_deepeval_run.paths import (
    AGENT_DEMO_ROOT,
    DEFAULT_REPORTS_DIR,
    ensure_agent_src_on_path,
)
from google_adk_deepeval_run.utils.runtime import load_env_files
from google_adk_deepeval_run.utils.scenarios import (
    ConversationTurn,
    Scenario,
    load_scenarios_from_file,
)
from google_adk_deepeval_run.evaluators.metrics import build_metrics_for_expectations


ensure_agent_src_on_path()

from runner import ScenarioRunner, ScenarioReport  # type: ignore  # noqa: E402


@dataclass
class MetricOutcome:
    metric_name: str
    score: float
    success: bool
    reason: str
    turn_index: int


@dataclass
class ScenarioEvaluationResult:
    scenario_name: str
    runner_success: bool
    execution_time: float
    messages: List[str]
    tools_used: List[str]
    errors: List[str]
    metadata: Dict[str, str]
    metrics: List[MetricOutcome] = field(default_factory=list)

    @property
    def metric_pass_rate(self) -> float:
        if not self.metrics:
            return 1.0
        passed = sum(1 for metric in self.metrics if metric.success)
        return passed / len(self.metrics)


@dataclass
class EvaluationSuiteResult:
    scenario_file: str
    agent_name: Optional[str]
    generated_at: str
    report_path: str
    scenario_results: List[ScenarioEvaluationResult]

    @property
    def overall_success_rate(self) -> float:
        if not self.scenario_results:
            return 1.0
        passed = sum(
            1
            for result in self.scenario_results
            if result.runner_success and result.metric_pass_rate == 1.0
        )
        return passed / len(self.scenario_results)

    def to_dict(self) -> Dict:
        return {
            "scenario_file": self.scenario_file,
            "agent_name": self.agent_name,
            "generated_at": self.generated_at,
            "report_path": self.report_path,
            "overall_success_rate": self.overall_success_rate,
            "scenario_results": [
                {
                    **{
                        key: value
                        for key, value in asdict(result).items()
                        if key != "metrics"
                    },
                    "metric_pass_rate": result.metric_pass_rate,
                    "metrics": [asdict(metric) for metric in result.metrics],
                }
                for result in self.scenario_results
            ],
        }


def _build_test_turns(scenario: Scenario, report: ScenarioReport) -> List[Tuple[int, ConversationTurn, LLMTestCase]]:
    turns = list(scenario.conversation)

    if not turns:
        turns = [
            ConversationTurn(
                user_input=scenario.error_message,
                expected_tools=None,
                expected_keywords=None,
                expected_links=None,
            )
        ]

    responses = report.messages or []
    context: List[str] = []
    if scenario.description:
        context.append(scenario.description)
    context.append(scenario.error_message)
    if scenario.programming_language:
        context.append(f"language: {scenario.programming_language}")
    if scenario.framework:
        context.append(f"framework: {scenario.framework}")

    turns_with_cases: List[Tuple[int, ConversationTurn, LLMTestCase]] = []

    for idx, turn in enumerate(turns):
        actual_output = responses[idx] if idx < len(responses) else ""
        test_case = LLMTestCase(
            input=turn.user_input or scenario.error_message,
            actual_output=actual_output,
            context=context,
        )
        turns_with_cases.append((idx, turn, test_case))

    return turns_with_cases


def _send_to_confident_ai(test_cases_with_metrics: List[Tuple[LLMTestCase, List]], test_run_name: str) -> bool:
    """Send evaluation results to Confident AI platform if API key is configured."""
    if not os.getenv("CONFIDENT_API_KEY"):
        return False
    
    # Disable automatic browser opening after uploading results
    os.environ.setdefault("CONFIDENT_OPEN_BROWSER", "false")
    
    try:
        # Group metrics by test case for the evaluate function
        # The evaluate function needs all metrics pre-measured
        test_cases_to_evaluate = []
        all_metrics = []
        
        for test_case, metrics in test_cases_with_metrics:
            if metrics:
                test_cases_to_evaluate.append(test_case)
                # Add each metric for this test case
                for metric in metrics:
                    all_metrics.append(metric)
        
        if test_cases_to_evaluate:
            # Use deepeval.evaluate to send results to Confident AI platform
            # This will automatically upload when CONFIDENT_API_KEY is set
            from deepeval.evaluate.configs import AsyncConfig, DisplayConfig
            
            evaluate(
                test_cases=test_cases_to_evaluate,
                metrics=all_metrics,
                identifier=test_run_name,
                async_config=AsyncConfig(run_async=False),
                display_config=DisplayConfig(
                    show_indicator=False,
                    print_results=False,
                    verbose_mode=False,
                ),
            )
            return True
    except Exception as e:
        print(f"Warning: Could not send results to Confident AI: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return False


async def run_deepeval_for_file(
    scenario_file: Path,
    *,
    agent_name: Optional[str] = None,
    output_dir: Optional[Path] = None,
    extra_env_files: Optional[Sequence[Path]] = None,
) -> EvaluationSuiteResult:
    scenario_path = scenario_file if scenario_file.is_absolute() else scenario_file.resolve()
    load_env_files(extra_env_files)

    scenarios = load_scenarios_from_file(scenario_path)

    runner = ScenarioRunner(agent_name=agent_name)
    await runner.setup()

    results: List[ScenarioEvaluationResult] = []
    confident_ai_data: List[Tuple[LLMTestCase, List]] = []

    try:
        for scenario in scenarios:
            report = await runner.run_scenario(scenario)
            scenario_result = ScenarioEvaluationResult(
                scenario_name=scenario.name,
                runner_success=report.success,
                execution_time=report.execution_time,
                messages=report.messages,
                tools_used=report.tools_used,
                errors=report.errors,
                metadata={k: str(v) for k, v in scenario.metadata.items()},
            )

            turns_with_cases = _build_test_turns(scenario, report)

            for turn_index, turn, test_case in turns_with_cases:
                metrics = build_metrics_for_expectations(
                    keywords=turn.expected_keywords,
                    links=turn.expected_links,
                    tools=turn.expected_tools,
                )

                for metric in metrics:
                    metric.measure(test_case, tools_used=report.tools_used)
                    scenario_result.metrics.append(
                        MetricOutcome(
                            metric_name=metric.__name__,
                            score=metric.score or 0.0,
                            success=metric.is_successful(),
                            reason=metric.reason or "",
                            turn_index=turn_index,
                        )
                    )
                
                # Collect data for Confident AI upload
                if metrics:
                    confident_ai_data.append((test_case, metrics))

            results.append(scenario_result)
    finally:
        await asyncio.sleep(0.1)

    reports_dir = output_dir or DEFAULT_REPORTS_DIR
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_name = f"{scenario_path.stem}_deepeval_{timestamp}.json"
    output_path = reports_dir / file_name

    evaluation = EvaluationSuiteResult(
        scenario_file=str(scenario_path),
        agent_name=agent_name,
        generated_at=datetime.utcnow().isoformat(),
        report_path=str(output_path),
        scenario_results=results,
    )

    output_path.write_text(json.dumps(evaluation.to_dict(), indent=2))

    # Send results to Confident AI platform if configured
    test_run_name = f"{scenario_path.stem}_{timestamp}"
    if _send_to_confident_ai(confident_ai_data, test_run_name):
        print(f"\n✓ Results uploaded to Confident AI platform (run: {test_run_name})")
    
    return evaluation


def run_deepeval_sync(**kwargs) -> EvaluationSuiteResult:
    return asyncio.run(run_deepeval_for_file(**kwargs))


__all__ = [
    "MetricOutcome",
    "ScenarioEvaluationResult",
    "EvaluationSuiteResult",
    "run_deepeval_for_file",
    "run_deepeval_sync",
]
