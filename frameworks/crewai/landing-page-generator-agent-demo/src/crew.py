"""
Crew orchestration for the Landing Page Generator.

This module defines the crew that coordinates agents to generate landing pages.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from crewai import Crew, Process
from .agents import LandingPageAgents
from .tasks import LandingPageTasks


class LandingPageCrew:
    """
    Orchestrates the landing page generation process using multiple agents.
    """

    def __init__(self,
                 model_name: str = "gpt-4",
                 temperature: float = 0.7,
                 verbose: bool = True,
                 output_dir: str = "./results/output",
                 workdir: str = "./results/workdir"):
        """
        Initialize the Landing Page Crew.

        Args:
            model_name: The LLM model to use
            temperature: Temperature setting for the model
            verbose: Whether to print verbose output
            output_dir: Directory for final output
            workdir: Working directory for intermediate files
        """
        self.model_name = model_name
        self.temperature = temperature
        self.verbose = verbose
        self.output_dir = Path(output_dir)
        self.workdir = Path(workdir)

        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.workdir.mkdir(parents=True, exist_ok=True)

        # Initialize agents and tasks factories
        self.agents_factory = LandingPageAgents(
            model_name=model_name,
            temperature=temperature,
            verbose=verbose
        )
        self.tasks_factory = LandingPageTasks()

        # Store execution results
        self.execution_results = {}

    def expand_idea_crew(self, idea: str) -> Crew:
        """
        Create a crew for expanding the initial idea.

        Args:
            idea: The initial landing page idea

        Returns:
            Crew configured for idea expansion
        """
        agent = self.agents_factory.idea_analyst()
        task = self.tasks_factory.expand_idea_task(idea)

        return Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose,
            output_log_file=str(self.workdir / "expand_idea.log")
        )

    def template_selection_crew(self, expanded_concept: Dict[str, Any]) -> Crew:
        """
        Create a crew for template selection.

        Args:
            expanded_concept: The expanded concept from idea analysis

        Returns:
            Crew configured for template selection
        """
        agent = self.agents_factory.template_selector()
        task = self.tasks_factory.select_template_task(expanded_concept)

        return Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose,
            output_log_file=str(self.workdir / "template_selection.log")
        )

    def content_creation_crew(self,
                             expanded_concept: Dict[str, Any],
                             template_plan: Dict[str, Any]) -> Crew:
        """
        Create a crew for content generation.

        Args:
            expanded_concept: The expanded concept
            template_plan: The template selection plan

        Returns:
            Crew configured for content creation
        """
        agents = [
            self.agents_factory.content_creator(),
            self.agents_factory.quality_assurance()
        ]

        tasks = [
            self.tasks_factory.create_content_task(expanded_concept, template_plan),
            self.tasks_factory.quality_review_task(expanded_concept, template_plan, {})
        ]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=self.verbose,
            output_log_file=str(self.workdir / "content_creation.log")
        )

    def parse_result(self, result: Any) -> Dict[str, Any]:
        """
        Parse crew execution result to extract JSON data.

        Args:
            result: The raw result from crew execution

        Returns:
            Parsed JSON data or error dict
        """
        try:
            # Convert result to string if needed
            result_str = str(result)

            # Try to find JSON in the result
            import re
            json_pattern = r'\{.*\}'
            json_match = re.search(json_pattern, result_str, re.DOTALL)

            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # If no JSON found, create a structured response
                return {
                    "raw_output": result_str,
                    "parsed": False
                }
        except Exception as e:
            return {
                "error": f"Failed to parse result: {str(e)}",
                "raw_output": str(result)
            }

    def generate_landing_page(self,
                            template_plan: Dict[str, Any],
                            content: Dict[str, Any]) -> str:
        """
        Generate the final landing page HTML.

        Args:
            template_plan: The template selection plan
            content: The generated content

        Returns:
            Path to the generated HTML file
        """
        try:
            # Create a basic HTML template if no template is selected
            html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; }}
        .hero {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 80px 0; text-align: center; }}
        .hero h1 {{ font-size: 3em; margin-bottom: 20px; }}
        .hero p {{ font-size: 1.3em; margin-bottom: 30px; }}
        .btn {{ display: inline-block; padding: 15px 40px; background: #fff; color: #667eea; text-decoration: none; border-radius: 5px; font-weight: bold; transition: transform 0.3s; }}
        .btn:hover {{ transform: translateY(-2px); }}
        .section {{ padding: 60px 0; }}
        .features {{ background: #f8f9fa; }}
        .feature-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin-top: 40px; }}
        .feature {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .feature h3 {{ color: #667eea; margin-bottom: 15px; }}
        .testimonials {{ background: white; }}
        .testimonial {{ background: #f8f9fa; padding: 30px; border-radius: 10px; margin: 20px 0; }}
        .footer {{ background: #2c3e50; color: white; padding: 40px 0; text-align: center; }}
    </style>
</head>
<body>
    <!-- Hero Section -->
    <section class="hero">
        <div class="container">
            <h1>{headline}</h1>
            <p>{subheadline}</p>
            <a href="#" class="btn">{cta_text}</a>
        </div>
    </section>

    <!-- Features Section -->
    <section class="section features">
        <div class="container">
            <h2 style="text-align: center; font-size: 2.5em; margin-bottom: 20px;">Key Features</h2>
            <div class="feature-grid">
                {features_html}
            </div>
        </div>
    </section>

    <!-- Testimonials Section -->
    <section class="section testimonials">
        <div class="container">
            <h2 style="text-align: center; font-size: 2.5em; margin-bottom: 40px;">What Our Customers Say</h2>
            {testimonials_html}
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 Your Company. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>"""

            # Extract content values
            hero_content = content.get('hero', {})
            features = content.get('features', [])
            testimonials = content.get('testimonials', [])

            # Generate features HTML
            features_html = ""
            for feature in features:
                features_html += f"""
                <div class="feature">
                    <h3>{feature.get('title', 'Feature')}</h3>
                    <p>{feature.get('description', 'Feature description')}</p>
                </div>"""

            # Generate testimonials HTML
            testimonials_html = ""
            for testimonial in testimonials:
                testimonials_html += f"""
                <div class="testimonial">
                    <p>"{testimonial.get('content', 'Great product!')}"</p>
                    <p><strong>- {testimonial.get('name', 'Customer')}, {testimonial.get('role', 'User')}</strong></p>
                </div>"""

            # Fill in the template
            html_content = html_template.format(
                title=hero_content.get('headline', 'Landing Page'),
                headline=hero_content.get('headline', 'Welcome to Our Product'),
                subheadline=hero_content.get('subheadline', 'The best solution for your needs'),
                cta_text=hero_content.get('cta_text', 'Get Started'),
                features_html=features_html,
                testimonials_html=testimonials_html
            )

            # Save the HTML file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"landing_page_{timestamp}.html"

            with open(output_file, 'w') as f:
                f.write(html_content)

            return str(output_file)

        except Exception as e:
            raise Exception(f"Failed to generate landing page: {str(e)}")

    def run(self, idea: str) -> Dict[str, Any]:
        """
        Execute the complete landing page generation process.

        Args:
            idea: The initial landing page idea from the user

        Returns:
            Dictionary containing execution results and output file path
        """
        try:
            print(f"\n{'='*50}")
            print(f"Starting Landing Page Generation for: {idea}")
            print(f"{'='*50}\n")

            # Phase 1: Expand the idea
            print("Phase 1: Expanding idea...")
            expand_crew = self.expand_idea_crew(idea)
            expand_result = expand_crew.kickoff()
            expanded_concept = self.parse_result(expand_result)
            self.execution_results['expanded_concept'] = expanded_concept

            # Save intermediate result
            with open(self.workdir / 'expanded_concept.json', 'w') as f:
                json.dump(expanded_concept, f, indent=2)

            # Phase 2: Select template
            print("\nPhase 2: Selecting template...")
            template_crew = self.template_selection_crew(expanded_concept)
            template_result = template_crew.kickoff()
            template_plan = self.parse_result(template_result)
            self.execution_results['template_plan'] = template_plan

            # Save intermediate result
            with open(self.workdir / 'template_plan.json', 'w') as f:
                json.dump(template_plan, f, indent=2)

            # Phase 3: Create content
            print("\nPhase 3: Creating content...")
            content_crew = self.content_creation_crew(expanded_concept, template_plan)
            content_result = content_crew.kickoff()
            content = self.parse_result(content_result)
            self.execution_results['content'] = content

            # Save intermediate result
            with open(self.workdir / 'content.json', 'w') as f:
                json.dump(content, f, indent=2)

            # Phase 4: Generate final landing page
            print("\nPhase 4: Generating landing page...")
            output_file = self.generate_landing_page(template_plan, content)
            self.execution_results['output_file'] = output_file

            print(f"\n{'='*50}")
            print(f"Landing Page Generation Complete!")
            print(f"Output file: {output_file}")
            print(f"{'='*50}\n")

            return {
                "success": True,
                "output_file": output_file,
                "execution_results": self.execution_results,
                "workdir": str(self.workdir)
            }

        except Exception as e:
            print(f"\nError during execution: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "execution_results": self.execution_results
            }

    def cleanup(self):
        """Clean up working directory."""
        try:
            if self.workdir.exists():
                shutil.rmtree(self.workdir)
                print(f"Cleaned up working directory: {self.workdir}")
        except Exception as e:
            print(f"Failed to clean up working directory: {str(e)}")