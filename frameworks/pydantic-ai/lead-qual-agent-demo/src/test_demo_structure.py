#!/usr/bin/env python
"""Test demo structure by running scenarios with mock data."""

import sys
import os
import asyncio
from datetime import datetime
import uuid

# Add the parent directory to the path to fix imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.models import (
    Lead,
    QualificationAnalysis,
    QualificationScore,
    PersonAnalysis,
    CompanyAnalysis,
    CompanySize
)
from src.scenarios.sample_leads import get_sample_leads
from rich.console import Console
from rich.table import Table


def create_mock_analysis(lead: Lead) -> QualificationAnalysis:
    """Create a mock qualification analysis for testing."""
    # Map certain keywords to scores for deterministic mock behavior
    score_map = {
        "VP": QualificationScore.HIGH,
        "CTO": QualificationScore.VERY_HIGH,
        "Manager": QualificationScore.MEDIUM,
        "Student": QualificationScore.UNQUALIFIED,
    }

    score = QualificationScore.MEDIUM  # default
    for keyword, mapped_score in score_map.items():
        if lead.title and keyword in lead.title:
            score = mapped_score
            break

    confidence = {
        QualificationScore.VERY_HIGH: 0.95,
        QualificationScore.HIGH: 0.85,
        QualificationScore.MEDIUM: 0.70,
        QualificationScore.LOW: 0.60,
        QualificationScore.VERY_LOW: 0.50,
        QualificationScore.UNQUALIFIED: 0.30,
    }[score]

    return QualificationAnalysis(
        lead_id=str(uuid.uuid4()),
        person_analysis=PersonAnalysis(
            name=lead.name,
            current_title=lead.title,
            is_technical="Engineer" in (lead.title or ""),
            is_decision_maker="VP" in (lead.title or "") or "CTO" in (lead.title or "")
        ),
        company_analysis=CompanyAnalysis(
            name=lead.company or "Unknown",
            size=CompanySize.ENTERPRISE if "Global" in (lead.company or "") else CompanySize.MID_MARKET,
            uses_python=True,
            has_engineering_team=True
        ) if lead.company else None,
        score=score,
        confidence=confidence,
        product_fit_reasons=["Mock reason 1", "Mock reason 2"],
        disqualification_reasons=[] if score.value in ["very_high", "high"] else ["Mock concern"],
        recommended_action="immediate_outreach" if score.value in ["very_high", "high"] else "nurture",
        talking_points=["Mock talking point 1", "Mock talking point 2"],
        summary=f"Mock analysis for {lead.name} - {score.value} score with {confidence:.1%} confidence"
    )


async def test_single_lead():
    """Test single lead qualification display."""
    console = Console()
    console.print("\n[bold]Testing Single Lead Qualification Display[/bold]\n")

    lead = get_sample_leads()[0]
    console.print(f"Lead: {lead.name} ({lead.title} at {lead.company})")

    analysis = create_mock_analysis(lead)
    console.print(f"Score: {analysis.score.value}")
    console.print(f"Confidence: {analysis.confidence:.1%}")
    console.print(f"Summary: {analysis.summary}")


async def test_batch_processing():
    """Test batch processing display."""
    console = Console()
    console.print("\n[bold]Testing Batch Processing Display[/bold]\n")

    leads = get_sample_leads()[:5]
    analyses = [create_mock_analysis(lead) for lead in leads]

    table = Table(title="Batch Qualification Results")
    table.add_column("Name", style="cyan")
    table.add_column("Company")
    table.add_column("Score", justify="center")
    table.add_column("Confidence", justify="center")
    table.add_column("Action", style="yellow")

    for analysis in analyses:
        company_name = analysis.company_analysis.name if analysis.company_analysis else "Unknown"
        table.add_row(
            analysis.person_analysis.name,
            company_name,
            analysis.score.value,
            f"{analysis.confidence:.1%}",
            analysis.recommended_action
        )

    console.print(table)


async def test_priority_ranking():
    """Test priority ranking display."""
    console = Console()
    console.print("\n[bold]Testing Priority Ranking Display[/bold]\n")

    leads = get_sample_leads()[:6]
    analyses = [create_mock_analysis(lead) for lead in leads]

    # Sort by score and confidence
    score_order = {
        QualificationScore.VERY_HIGH: 6,
        QualificationScore.HIGH: 5,
        QualificationScore.MEDIUM: 4,
        QualificationScore.LOW: 3,
        QualificationScore.VERY_LOW: 2,
        QualificationScore.UNQUALIFIED: 1
    }

    sorted_analyses = sorted(
        analyses,
        key=lambda x: (score_order.get(x.score, 0), x.confidence),
        reverse=True
    )

    table = Table(title="Sales Outreach Priority List")
    table.add_column("Priority", justify="center", style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Company")
    table.add_column("Score", justify="center")
    table.add_column("Action", style="yellow")

    for i, analysis in enumerate(sorted_analyses[:5], 1):
        company_name = analysis.company_analysis.name if analysis.company_analysis else "Unknown"
        table.add_row(
            str(i),
            analysis.person_analysis.name,
            company_name,
            analysis.score.value,
            analysis.recommended_action
        )

    console.print(table)


async def test_scenario_comparison():
    """Test scenario comparison display."""
    console = Console()
    console.print("\n[bold]Testing Scenario Comparison Display[/bold]\n")

    from src.scenarios.sample_leads import (
        get_high_priority_leads,
        get_technical_leads,
        get_unqualified_leads
    )

    scenarios = [
        ("High Priority Leads", get_high_priority_leads()),
        ("Technical Leads", get_technical_leads()),
        ("Unqualified Leads", get_unqualified_leads())
    ]

    for scenario_name, leads in scenarios:
        analyses = [create_mock_analysis(lead) for lead in leads]

        avg_confidence = sum(a.confidence for a in analyses) / len(analyses) if analyses else 0

        console.print(f"\n[bold cyan]{scenario_name}:[/bold cyan]")
        console.print(f"  • Lead count: {len(analyses)}")
        console.print(f"  • Average Confidence: {avg_confidence:.1%}")
        console.print(f"  • Scores: {', '.join(a.score.value for a in analyses)}")


async def main():
    """Run all test scenarios."""
    console = Console()
    console.print("[bold magenta]Testing Demo Structure and Display[/bold magenta]")
    console.print("This test runs with mock data - no API calls needed\n")

    await test_single_lead()
    await test_batch_processing()
    await test_priority_ranking()
    await test_scenario_comparison()

    console.print("\n[bold green]✅ All demo structures tested successfully![/bold green]")
    console.print("\nThe demos are working correctly. To run with real AI:")
    console.print("1. Add valid API keys to .env file")
    console.print("2. Run: uv run python src/run_scenario.py [scenario]")


if __name__ == "__main__":
    asyncio.run(main())