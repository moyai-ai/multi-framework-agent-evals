"""Main entry point for the Lead Qualification Agent Demo."""

import asyncio
import os
from typing import Optional
from rich.console import Console
from dotenv import load_dotenv

from agent.lead_qualifier import LeadQualificationAgent
from agent.models import Lead
from scenarios.demo_runner import DemoRunner
from scenarios.sample_leads import get_sample_leads


def setup_environment():
    """Set up environment variables and API keys."""
    load_dotenv()

    # Check for required API keys
    if not os.getenv("OPENAI_API_KEY"):
        console = Console()
        console.print("[red]Error: OPENAI_API_KEY environment variable not set![/red]")
        console.print("Please set your OpenAI API key in a .env file or environment variable.")
        return False

    if not os.getenv("LINKUP_API_KEY"):
        console = Console()
        console.print("[yellow]Warning: LINKUP_API_KEY environment variable not set![/yellow]")
        console.print("The agent will not be able to perform web searches without this key.")
        console.print("Get your API key from https://www.linkup.so/")
        response = input("\nContinue without Linkup API key? (y/n): ")
        if response.lower() != 'y':
            return False

    return True


async def quick_demo():
    """Run a quick demonstration of the lead qualification agent."""
    console = Console()

    console.print("[bold blue]Lead Qualification Agent - Quick Demo[/bold blue]\n")

    # Create a sample lead
    lead = Lead(
        name="John Smith",
        email="john.smith@techstartup.example.com",
        company="TechStartup Inc",
        title="VP of Engineering",
        source="conference",
        additional_info={
            "met_at": "AI Summit 2024",
            "interested_in": "ML monitoring tools",
        }
    )

    console.print("[cyan]Qualifying the following lead:[/cyan]")
    console.print(f"Name: {lead.name}")
    console.print(f"Company: {lead.company}")
    console.print(f"Title: {lead.title}\n")

    # Initialize agent
    try:
        agent = LeadQualificationAgent()
        analysis = await agent.qualify_lead(lead)

        # Display results
        console.print("\n[bold green]Qualification Complete![/bold green]\n")
        console.print(f"Score: {analysis.score.value.upper()}")
        console.print(f"Confidence: {analysis.confidence:.1%}")
        console.print(f"Recommended Action: {analysis.recommended_action}")
        console.print(f"\nSummary: {analysis.summary}")

        if analysis.talking_points:
            console.print("\n[bold]Suggested Talking Points:[/bold]")
            for point in analysis.talking_points[:3]:
                console.print(f"• {point}")

    except Exception as e:
        console.print(f"[red]Error during qualification: {e}[/red]")


async def interactive_mode():
    """Run the agent in interactive mode."""
    console = Console()

    console.print("[bold blue]Lead Qualification Agent - Interactive Mode[/bold blue]\n")

    # Get lead information from user
    console.print("Enter lead information:")
    name = input("Name: ")
    email = input("Email: ")
    company = input("Company (optional): ")
    title = input("Title (optional): ")
    linkedin = input("LinkedIn URL (optional): ")

    lead = Lead(
        name=name,
        email=email,
        company=company if company else None,
        title=title if title else None,
        linkedin_url=linkedin if linkedin else None,
        source="manual_entry"
    )

    console.print("\n[cyan]Qualifying lead...[/cyan]")

    try:
        agent = LeadQualificationAgent()
        analysis = await agent.qualify_lead(lead)

        # Display detailed results
        runner = DemoRunner()
        runner.print_analysis(analysis)

    except Exception as e:
        console.print(f"[red]Error during qualification: {e}[/red]")


async def main():
    """Main entry point for the application."""
    console = Console()

    # Display banner
    console.print("""
[bold cyan]╔══════════════════════════════════════════════╗
║     Lead Qualification Agent Demo           ║
║     Powered by Pydantic AI & Linkup.so      ║
╚══════════════════════════════════════════════╝[/bold cyan]
    """)

    # Setup environment
    if not setup_environment():
        return

    # Main menu
    while True:
        console.print("\n[bold]Main Menu:[/bold]")
        console.print("1. Quick Demo (pre-configured lead)")
        console.print("2. Interactive Mode (enter your own lead)")
        console.print("3. Full Demo Suite (multiple scenarios)")
        console.print("4. Batch Processing Demo")
        console.print("0. Exit\n")

        choice = input("Select option (0-4): ")

        if choice == "1":
            await quick_demo()
        elif choice == "2":
            await interactive_mode()
        elif choice == "3":
            runner = DemoRunner()
            await runner.run_all_demos()
        elif choice == "4":
            runner = DemoRunner()
            await runner.run_batch_demo(get_sample_leads()[:5])
        elif choice == "0":
            console.print("[yellow]Goodbye![/yellow]")
            break
        else:
            console.print("[red]Invalid option. Please try again.[/red]")

        if choice != "0":
            input("\nPress Enter to return to menu...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]Interrupted by user. Exiting...[/yellow]")