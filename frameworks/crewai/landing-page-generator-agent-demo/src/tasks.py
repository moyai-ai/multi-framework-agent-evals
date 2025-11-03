"""
Task definitions for the Landing Page Generator Crew.

This module defines the tasks that agents will execute to generate landing pages.
"""

from typing import Optional, Dict, Any
from crewai import Task
from .agents import LandingPageAgents


class LandingPageTasks:
    """Factory class for creating landing page generation tasks."""

    def __init__(self):
        """Initialize the tasks factory."""
        self.agents = LandingPageAgents()

    def expand_idea_task(self, idea: str) -> Task:
        """
        Create the task for expanding and researching the initial idea.

        Args:
            idea: The initial concept/idea from the user

        Returns:
            Task for idea expansion
        """
        return Task(
            description=f"""
            Research and expand the following landing page idea into a comprehensive concept:

            Idea: {idea}

            Your task is to:
            1. Research the market and competitors for this idea
            2. Identify the target audience and their pain points
            3. Define key features and benefits to highlight
            4. Determine the unique selling proposition (USP)
            5. Suggest the primary call-to-action (CTA)
            6. Recommend the overall tone and style

            Provide a detailed expansion that includes:
            - Business overview
            - Target audience profile
            - Key features (at least 3-5)
            - Main benefits
            - Unique selling points
            - Recommended sections for the landing page
            - Suggested color scheme and visual style
            """,
            agent=self.agents.idea_analyst(),
            expected_output="""A comprehensive JSON document containing:
            - expanded_concept: Detailed description of the idea
            - target_audience: Demographics and psychographics
            - features: List of key features
            - benefits: List of main benefits
            - usp: Unique selling proposition
            - sections: Recommended landing page sections
            - style_guide: Visual and tone recommendations
            """,
            output_file="results/expanded_idea.json"
        )

    def select_template_task(self, expanded_concept: Dict[str, Any]) -> Task:
        """
        Create the task for selecting the appropriate template.

        Args:
            expanded_concept: The expanded concept from the idea analyst

        Returns:
            Task for template selection
        """
        return Task(
            description=f"""
            Based on the expanded concept, select and customize the most appropriate template:

            Concept Details:
            {expanded_concept}

            Your task is to:
            1. Analyze available templates in the templates directory
            2. Select the best matching template for the concept
            3. Identify sections that need customization
            4. Plan the layout modifications needed
            5. Determine component requirements

            Consider:
            - Target audience preferences
            - Industry best practices
            - Conversion optimization principles
            - Mobile responsiveness
            - Loading performance
            """,
            agent=self.agents.template_selector(),
            expected_output="""A JSON document containing:
            - selected_template: Name/path of the selected template
            - customization_plan: List of modifications needed
            - sections_mapping: How concept sections map to template sections
            - color_scheme: Recommended colors (primary, secondary, accent)
            - typography: Font recommendations
            - components_needed: List of UI components to use
            """,
            output_file="results/template_selection.json"
        )

    def create_content_task(self, expanded_concept: Dict[str, Any], template_plan: Dict[str, Any]) -> Task:
        """
        Create the task for generating landing page content.

        Args:
            expanded_concept: The expanded concept
            template_plan: The template selection and customization plan

        Returns:
            Task for content creation
        """
        return Task(
            description=f"""
            Create compelling content for the landing page based on the concept and template:

            Concept: {expanded_concept}
            Template Plan: {template_plan}

            Generate content for:
            1. Hero section (headline, subheadline, CTA)
            2. Features section (feature titles and descriptions)
            3. Benefits section (benefit statements)
            4. About/Story section
            5. Testimonials (create realistic examples)
            6. FAQ section (common questions and answers)
            7. Footer content
            8. Meta tags (title, description, keywords)

            Ensure all content:
            - Follows conversion copywriting best practices
            - Maintains consistent tone and voice
            - Includes power words and emotional triggers
            - Has clear and compelling CTAs
            - Is SEO-optimized
            """,
            agent=self.agents.content_creator(),
            expected_output="""A JSON document containing:
            - hero: Object with headline, subheadline, cta_text
            - features: Array of feature objects with title, description, icon
            - benefits: Array of benefit statements
            - about: About section content
            - testimonials: Array of testimonial objects
            - faq: Array of FAQ objects with question and answer
            - footer: Footer content including links and copyright
            - meta: SEO meta tags
            """,
            output_file="results/page_content.json"
        )

    def quality_review_task(self,
                          expanded_concept: Dict[str, Any],
                          template_plan: Dict[str, Any],
                          content: Dict[str, Any]) -> Task:
        """
        Create the task for quality assurance and final review.

        Args:
            expanded_concept: The expanded concept
            template_plan: The template selection plan
            content: The generated content

        Returns:
            Task for quality review
        """
        return Task(
            description=f"""
            Review and ensure the quality of the generated landing page:

            Concept: {expanded_concept}
            Template: {template_plan}
            Content: {content}

            Your review should check:
            1. Content consistency and alignment with concept
            2. Grammar, spelling, and readability
            3. Call-to-action effectiveness
            4. Visual hierarchy and layout logic
            5. Mobile responsiveness considerations
            6. SEO optimization
            7. Loading performance factors
            8. Accessibility standards

            Provide:
            - Quality score (0-100)
            - List of issues found (if any)
            - Improvement suggestions
            - Final approval status
            """,
            agent=self.agents.quality_assurance(),
            expected_output="""A JSON document containing:
            - quality_score: Overall quality score (0-100)
            - issues: Array of identified issues with severity levels
            - suggestions: Array of improvement suggestions
            - approval_status: 'approved' or 'needs_revision'
            - final_notes: Any additional notes or comments
            """,
            output_file="results/quality_review.json"
        )

    def generate_landing_page_task(self,
                                  template_plan: Dict[str, Any],
                                  content: Dict[str, Any]) -> Task:
        """
        Create the task for generating the final landing page HTML.

        Args:
            template_plan: The template selection plan
            content: The approved content

        Returns:
            Task for generating the final landing page
        """
        return Task(
            description=f"""
            Generate the final landing page HTML using the selected template and content:

            Template: {template_plan}
            Content: {content}

            Your task is to:
            1. Load the selected template
            2. Inject the content into appropriate sections
            3. Apply the recommended styling
            4. Ensure proper HTML structure
            5. Add necessary meta tags
            6. Include responsive design classes
            7. Optimize for performance

            The output should be a complete, ready-to-deploy landing page.
            """,
            agent=self.agents.content_creator(),
            expected_output="""Complete HTML file with:
            - Proper DOCTYPE and HTML structure
            - Head section with meta tags and styles
            - Body with all content sections
            - Inline CSS or linked stylesheets
            - JavaScript for interactions (if needed)
            - Comments for section identification
            """,
            output_file="results/landing_page.html"
        )


def create_landing_page_tasks(idea: str) -> Dict[str, Task]:
    """
    Create all tasks needed for landing page generation.

    Args:
        idea: The initial landing page idea

    Returns:
        Dictionary of task names to Task objects
    """
    factory = LandingPageTasks()

    # Create placeholder dictionaries for task chaining
    # In actual execution, these would be replaced with real outputs
    placeholder_concept = {"concept": "placeholder"}
    placeholder_template = {"template": "placeholder"}
    placeholder_content = {"content": "placeholder"}

    return {
        "expand_idea": factory.expand_idea_task(idea),
        "select_template": factory.select_template_task(placeholder_concept),
        "create_content": factory.create_content_task(placeholder_concept, placeholder_template),
        "quality_review": factory.quality_review_task(
            placeholder_concept,
            placeholder_template,
            placeholder_content
        ),
        "generate_page": factory.generate_landing_page_task(placeholder_template, placeholder_content)
    }