"""Demo runner for lead qualification scenarios."""

import asyncio
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..agent.lead_qualifier import LeadQualificationAgent
from ..agent.models import Lead, QualificationAnalysis, QualificationScore
from .sample_leads import (
    get_sample_leads,
    get_high_priority_leads,
    get_technical_leads,
    get_unqualified_leads,
)


class DemoRunner:
    """Runner for demonstrating lead qualification scenarios."""

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the demo runner.

        Args:
            model: OpenAI model to use for the agent
        """
        self.console = Console()
        self.agent = LeadQualificationAgent(model=model)
        # Ensure reports directory exists
        self.reports_dir = Path(__file__).parent.parent.parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)

    def save_report(self, report_data: Dict[str, Any], filename: str):
        """
        Save a JSON report to the reports directory.

        Args:
            report_data: Dictionary containing report data
            filename: Name of the file (will have .json appended if not present)
        """
        if not filename.endswith('.json'):
            filename += '.json'
        
        report_path = self.reports_dir / filename
        report_data['report_timestamp'] = datetime.now().isoformat()
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str, ensure_ascii=False)
        
        self.console.print(f"[dim]Report saved to: {report_path}[/dim]")

    def print_header(self, title: str):
        """Print a formatted header."""
        self.console.print(f"\n[bold blue]{'=' * 60}[/bold blue]")
        self.console.print(f"[bold white]{title.center(60)}[/bold white]")
        self.console.print(f"[bold blue]{'=' * 60}[/bold blue]\n")

    def print_lead_info(self, lead: Lead):
        """Print lead information in a formatted panel."""
        info_text = f"""[bold]Name:[/bold] {lead.name}
[bold]Email:[/bold] {lead.email}
[bold]Company:[/bold] {lead.company or 'Unknown'}
[bold]Title:[/bold] {lead.title or 'Unknown'}
[bold]Source:[/bold] {lead.source}"""

        if lead.linkedin_url:
            info_text += f"\n[bold]LinkedIn:[/bold] {lead.linkedin_url}"

        if lead.additional_info:
            info_text += "\n[bold]Additional Info:[/bold]"
            for key, value in lead.additional_info.items():
                info_text += f"\n  • {key}: {value}"

        panel = Panel(info_text, title="Lead Information", border_style="cyan")
        self.console.print(panel)

    def print_analysis(self, analysis: QualificationAnalysis):
        """Print qualification analysis in a formatted way."""
        # Score color mapping
        score_colors = {
            QualificationScore.VERY_HIGH: "bright_green",
            QualificationScore.HIGH: "green",
            QualificationScore.MEDIUM: "yellow",
            QualificationScore.LOW: "red",
            QualificationScore.VERY_LOW: "bright_red",
            QualificationScore.UNQUALIFIED: "grey50",
        }

        score_color = score_colors.get(analysis.score, "white")

        # Create analysis panel
        analysis_text = f"""[bold]Score:[/bold] [{score_color}]{analysis.score.value.upper()}[/{score_color}]
[bold]Confidence:[/bold] {analysis.confidence:.1%}
[bold]Recommended Action:[/bold] {analysis.recommended_action}

[bold]Summary:[/bold]
{analysis.summary}"""

        # Add person analysis
        if analysis.person_analysis:
            analysis_text += f"\n\n[bold cyan]Person Analysis:[/bold cyan]"
            analysis_text += f"\n• Current Role: {analysis.person_analysis.current_title or 'Unknown'}"
            analysis_text += f"\n• Seniority: {analysis.person_analysis.seniority or 'Unknown'}"
            analysis_text += f"\n• Technical: {'Yes' if analysis.person_analysis.is_technical else 'No'}"
            analysis_text += f"\n• Decision Maker: {'Yes' if analysis.person_analysis.is_decision_maker else 'No'}"

        # Add company analysis
        if analysis.company_analysis:
            analysis_text += f"\n\n[bold cyan]Company Analysis:[/bold cyan]"
            analysis_text += f"\n• Company: {analysis.company_analysis.name}"
            analysis_text += f"\n• Size: {analysis.company_analysis.size.value}"
            analysis_text += f"\n• Industry: {analysis.company_analysis.industry or 'Unknown'}"
            analysis_text += f"\n• Uses Python: {'Yes' if analysis.company_analysis.uses_python else 'No'}"
            analysis_text += f"\n• Has Engineering Team: {'Yes' if analysis.company_analysis.has_engineering_team else 'No'}"

        # Add qualification reasons
        if analysis.product_fit_reasons:
            analysis_text += f"\n\n[bold green]Product Fit Reasons:[/bold green]"
            for reason in analysis.product_fit_reasons:
                analysis_text += f"\n✓ {reason}"

        if analysis.disqualification_reasons:
            analysis_text += f"\n\n[bold red]Concerns:[/bold red]"
            for reason in analysis.disqualification_reasons:
                analysis_text += f"\n✗ {reason}"

        # Add talking points
        if analysis.talking_points:
            analysis_text += f"\n\n[bold]Talking Points:[/bold]"
            for i, point in enumerate(analysis.talking_points, 1):
                analysis_text += f"\n{i}. {point}"

        panel = Panel(analysis_text, title="Qualification Analysis", border_style="green")
        self.console.print(panel)

    def print_batch_summary(self, analyses: List[QualificationAnalysis]):
        """Print a summary table of batch qualification results."""
        table = Table(title="Batch Qualification Summary", show_header=True)

        table.add_column("Name", style="cyan")
        table.add_column("Company", style="white")
        table.add_column("Score", justify="center")
        table.add_column("Confidence", justify="center")
        table.add_column("Action", style="yellow")

        score_colors = {
            QualificationScore.VERY_HIGH: "bright_green",
            QualificationScore.HIGH: "green",
            QualificationScore.MEDIUM: "yellow",
            QualificationScore.LOW: "red",
            QualificationScore.VERY_LOW: "bright_red",
            QualificationScore.UNQUALIFIED: "grey50",
        }

        for analysis in analyses:
            score_color = score_colors.get(analysis.score, "white")
            company_name = analysis.company_analysis.name if analysis.company_analysis else "Unknown"

            table.add_row(
                analysis.person_analysis.name,
                company_name,
                f"[{score_color}]{analysis.score.value}[/{score_color}]",
                f"{analysis.confidence:.1%}",
                analysis.recommended_action,
            )

        self.console.print(table)

    async def run_single_lead_demo(self, lead: Lead):
        """
        Run a demo for a single lead qualification.

        Args:
            lead: Lead to qualify
        """
        self.print_header("Single Lead Qualification Demo")
        self.print_lead_info(lead)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Qualifying lead...", total=None)

            try:
                analysis = await self.agent.qualify_lead(lead)
                progress.update(task, completed=True)
            except Exception as e:
                self.console.print(f"[red]Error qualifying lead: {e}[/red]")
                return

        self.print_analysis(analysis)
        
        # Save report
        report_data = {
            "scenario": "single_lead",
            "lead": lead.model_dump(mode='json'),
            "analysis": analysis.model_dump(mode='json'),
        }
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_report(report_data, f"single_lead_{timestamp}.json")
        
        return analysis

    async def run_batch_demo(self, leads: Optional[List[Lead]] = None):
        """
        Run a demo for batch lead qualification.

        Args:
            leads: List of leads to qualify (uses sample leads if not provided)
        """
        if leads is None:
            leads = get_sample_leads()[:5]  # Use first 5 sample leads

        self.print_header(f"Batch Lead Qualification Demo ({len(leads)} leads)")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task(f"[cyan]Qualifying {len(leads)} leads...", total=None)

            try:
                analyses = await self.agent.qualify_batch(leads, parallel=True)
                progress.update(task, completed=True)
            except Exception as e:
                self.console.print(f"[red]Error in batch qualification: {e}[/red]")
                return

        self.print_batch_summary(analyses)

        # Show high-value leads
        high_value = self.agent.get_high_value_leads(analyses)
        if high_value:
            self.console.print(f"\n[bold green]Found {len(high_value)} high-value leads![/bold green]")

        # Save report
        report_data = {
            "scenario": "batch",
            "total_leads": len(leads),
            "leads": [lead.model_dump(mode='json') for lead in leads],
            "analyses": [analysis.model_dump(mode='json') for analysis in analyses],
            "high_value_count": len(high_value) if high_value else 0,
        }
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_report(report_data, f"batch_{timestamp}.json")

        return analyses

    async def run_priority_ranking_demo(self):
        """Run a demo showing lead prioritization."""
        self.print_header("Lead Priority Ranking Demo")

        leads = get_sample_leads()[:6]  # Use 6 sample leads

        self.console.print("[cyan]Qualifying leads for prioritization...[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task(f"[cyan]Analyzing {len(leads)} leads...", total=None)

            try:
                analyses = await self.agent.qualify_batch(leads, parallel=True)
                progress.update(task, completed=True)
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                return

        # Generate priority list
        priority_list = self.agent.generate_outreach_priority_list(analyses)

        # Display priority table
        table = Table(title="Sales Outreach Priority List", show_header=True)
        table.add_column("Priority", justify="center", style="bold")
        table.add_column("Name", style="cyan")
        table.add_column("Company")
        table.add_column("Score", justify="center")
        table.add_column("Confidence", justify="center")
        table.add_column("Next Action", style="yellow")

        for item in priority_list:
            score_colors = {
                QualificationScore.VERY_HIGH: "bright_green",
                QualificationScore.HIGH: "green",
                QualificationScore.MEDIUM: "yellow",
                QualificationScore.LOW: "red",
                QualificationScore.VERY_LOW: "bright_red",
                QualificationScore.UNQUALIFIED: "grey50",
            }
            score_color = score_colors.get(item["score"], "white")

            table.add_row(
                str(item["priority"]),
                item["name"],
                item["company"],
                f"[{score_color}]{item['score'].value}[/{score_color}]",
                f"{item['confidence']:.1%}",
                item["recommended_action"],
            )

        self.console.print(table)

        # Show top priority details
        if priority_list:
            self.console.print("\n[bold]Top Priority Lead:[/bold]")
            top = priority_list[0]
            self.console.print(f"• {top['name']} from {top['company']}")
            self.console.print(f"• Key Talking Point: {top['key_talking_point']}")

        # Save report
        # Convert priority list items to JSON-serializable format
        serializable_priority_list = []
        for item in priority_list:
            serializable_item = {
                "priority": item["priority"],
                "name": item["name"],
                "company": item["company"],
                "score": item["score"].value if hasattr(item["score"], 'value') else str(item["score"]),
                "confidence": item["confidence"],
                "recommended_action": item["recommended_action"],
                "key_talking_point": item.get("key_talking_point", ""),
            }
            serializable_priority_list.append(serializable_item)
        
        report_data = {
            "scenario": "priority_ranking",
            "total_leads": len(leads),
            "priority_list": serializable_priority_list,
            "analyses": [analysis.model_dump(mode='json') for analysis in analyses],
        }
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_report(report_data, f"priority_ranking_{timestamp}.json")

        return priority_list

    async def run_scenario_comparison(self):
        """Run a demo comparing different types of leads."""
        self.print_header("Lead Type Comparison Demo")

        scenarios = [
            ("High Priority Leads", get_high_priority_leads()),
            ("Technical Leads", get_technical_leads()),
            ("Unqualified Leads", get_unqualified_leads()),
        ]

        all_analyses = {}

        for scenario_name, leads in scenarios:
            self.console.print(f"\n[bold cyan]Analyzing {scenario_name}...[/bold cyan]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task(f"[cyan]Processing {len(leads)} leads...", total=None)

                try:
                    analyses = await self.agent.qualify_batch(leads, parallel=True)
                    all_analyses[scenario_name] = analyses
                    progress.update(task, completed=True)
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
                    continue

        # Display comparison
        self.console.print("\n[bold]Scenario Comparison Results:[/bold]\n")

        for scenario_name, analyses in all_analyses.items():
            avg_confidence = sum(a.confidence for a in analyses) / len(analyses) if analyses else 0

            # Count by score
            score_counts = {}
            for analysis in analyses:
                score_counts[analysis.score] = score_counts.get(analysis.score, 0) + 1

            self.console.print(f"[bold cyan]{scenario_name}:[/bold cyan]")
            self.console.print(f"  • Average Confidence: {avg_confidence:.1%}")
            self.console.print(f"  • Score Distribution:")
            for score, count in score_counts.items():
                self.console.print(f"    - {score.value}: {count}")

        # Save report
        serializable_analyses = {}
        for scenario_name, analyses in all_analyses.items():
            serializable_analyses[scenario_name] = {
                "analyses": [analysis.model_dump(mode='json') for analysis in analyses],
                "summary": {
                    "count": len(analyses),
                    "avg_confidence": sum(a.confidence for a in analyses) / len(analyses) if analyses else 0,
                    "score_distribution": {
                        score.value: sum(1 for a in analyses if a.score == score)
                        for score in QualificationScore
                    }
                }
            }
        
        report_data = {
            "scenario": "comparison",
            "scenarios": serializable_analyses,
        }
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_report(report_data, f"comparison_{timestamp}.json")

        return all_analyses

    async def run_all_demos(self, interactive: bool = True):
        """
        Run all demonstration scenarios.
        
        Args:
            interactive: If True, pause for user input between demos. If False, run continuously.
        """
        demos = [
            ("Single Lead", self.run_single_lead_demo(get_sample_leads()[0])),
            ("Batch Processing", self.run_batch_demo()),
            ("Priority Ranking", self.run_priority_ranking_demo()),
            ("Scenario Comparison", self.run_scenario_comparison()),
        ]

        results = []
        for name, demo_coro in demos:
            self.console.print(f"\n[bold magenta]Running: {name}[/bold magenta]")
            result = await demo_coro
            results.append({"name": name, "completed": True})
            if interactive:
                self.console.print("\n[dim]Press Enter to continue to next demo...[/dim]")
                input()
            else:
                self.console.print("")
        
        # Save summary report for "all" scenario
        report_data = {
            "scenario": "all",
            "total_scenarios": len(demos),
            "completed_scenarios": [r["name"] for r in results],
        }
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_report(report_data, f"all_scenarios_{timestamp}.json")


async def main():
    """Main function to run the demo."""
    runner = DemoRunner()

    # Menu
    console = Console()
    console.print("[bold]Lead Qualification Agent Demo[/bold]\n")
    console.print("1. Single Lead Qualification")
    console.print("2. Batch Lead Processing")
    console.print("3. Priority Ranking")
    console.print("4. Scenario Comparison")
    console.print("5. Run All Demos")
    console.print("0. Exit\n")

    choice = input("Select demo (0-5): ")

    if choice == "1":
        lead = get_sample_leads()[0]
        await runner.run_single_lead_demo(lead)
    elif choice == "2":
        await runner.run_batch_demo()
    elif choice == "3":
        await runner.run_priority_ranking_demo()
    elif choice == "4":
        await runner.run_scenario_comparison()
    elif choice == "5":
        await runner.run_all_demos()
    else:
        console.print("[yellow]Exiting...[/yellow]")


if __name__ == "__main__":
    asyncio.run(main())