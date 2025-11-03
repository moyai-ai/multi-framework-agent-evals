"""
Agent definitions for the Landing Page Generator Crew.

This module defines the AI agents that collaborate to generate landing pages.
"""

from typing import List, Optional
from crewai import Agent
from .tools import (
    SearchTool,
    FileOperationsTool,
    TemplateManagerTool,
    ContentGeneratorTool,
    WebScrapingTool
)


class LandingPageAgents:
    """Factory class for creating landing page generation agents."""

    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.7, verbose: bool = True):
        """
        Initialize the agents factory.

        Args:
            model_name: The LLM model to use for agents
            temperature: Temperature setting for the model
            verbose: Whether to print verbose output
        """
        self.model_name = model_name
        self.temperature = temperature
        self.verbose = verbose

        # Initialize tools (tools from @tool decorator are already Tool objects)
        self.search_tool = SearchTool
        self.file_ops_tool = FileOperationsTool
        self.template_tool = TemplateManagerTool
        self.content_tool = ContentGeneratorTool
        self.scraping_tool = WebScrapingTool

    def idea_analyst(self) -> Agent:
        """
        Create the Idea Analyst agent.

        This agent researches and expands the initial concept.
        """
        return Agent(
            role="Senior Idea Analyst",
            goal="Research and expand the initial concept into a comprehensive landing page plan",
            backstory="""You are an experienced business analyst and market researcher with deep
            expertise in understanding customer needs and market trends. You excel at taking raw
            ideas and transforming them into detailed, actionable concepts. Your research skills
            help you identify key features, benefits, and unique selling propositions that will
            make the landing page compelling.""",
            tools=[self.search_tool, self.scraping_tool],
            allow_delegation=False,
            verbose=self.verbose,
            model=self.model_name,
            temperature=self.temperature
        )

    def template_selector(self) -> Agent:
        """
        Create the Template Selector agent.

        This agent evaluates and selects the best template for the concept.
        """
        return Agent(
            role="Senior UX/UI Designer",
            goal="Select the most appropriate template based on the expanded concept",
            backstory="""You are a seasoned UX/UI designer with over 10 years of experience in
            web design and user experience. You have an eye for design patterns that convert
            visitors into customers. Your expertise includes understanding which layouts, color
            schemes, and components work best for different types of businesses and audiences.""",
            tools=[self.template_tool, self.file_ops_tool],
            allow_delegation=False,
            verbose=self.verbose,
            model=self.model_name,
            temperature=self.temperature
        )

    def content_creator(self) -> Agent:
        """
        Create the Content Creator agent.

        This agent generates compelling content for the landing page.
        """
        return Agent(
            role="Senior Content Strategist",
            goal="Create compelling, conversion-focused content for the landing page",
            backstory="""You are a master copywriter and content strategist with expertise in
            conversion optimization. You understand the psychology of persuasion and know how to
            craft headlines, body copy, and calls-to-action that drive results. Your writing is
            clear, engaging, and tailored to the target audience.""",
            tools=[self.content_tool, self.file_ops_tool],
            allow_delegation=False,
            verbose=self.verbose,
            model=self.model_name,
            temperature=self.temperature
        )

    def quality_assurance(self) -> Agent:
        """
        Create the Quality Assurance agent.

        This agent reviews and ensures the quality of the generated landing page.
        """
        return Agent(
            role="Senior QA Engineer",
            goal="Review and ensure the quality, consistency, and effectiveness of the landing page",
            backstory="""You are a meticulous QA engineer with a background in both technical
            testing and user experience evaluation. You have a keen eye for detail and ensure that
            every element of the landing page works harmoniously. You check for consistency in
            messaging, proper HTML structure, responsive design, and overall user experience.""",
            tools=[self.file_ops_tool, self.template_tool],
            allow_delegation=False,
            verbose=self.verbose,
            model=self.model_name,
            temperature=self.temperature
        )

    def get_all_agents(self) -> List[Agent]:
        """
        Get all agents for the landing page generation crew.

        Returns:
            List of all configured agents
        """
        return [
            self.idea_analyst(),
            self.template_selector(),
            self.content_creator(),
            self.quality_assurance()
        ]


# Agent registry for easy access
AGENTS = {
    "idea_analyst": "Idea Analyst",
    "template_selector": "Template Selector",
    "content_creator": "Content Creator",
    "quality_assurance": "Quality Assurance"
}


def get_initial_agent() -> Agent:
    """
    Get the initial agent for the crew (Idea Analyst).

    Returns:
        The initial agent instance
    """
    factory = LandingPageAgents()
    return factory.idea_analyst()


def get_agent_by_name(name: str, model_name: str = "gpt-4") -> Optional[Agent]:
    """
    Get an agent by its name.

    Args:
        name: The name or partial name of the agent
        model_name: The model to use for the agent

    Returns:
        The agent instance if found, None otherwise
    """
    factory = LandingPageAgents(model_name=model_name)
    name_lower = name.lower()

    if "idea" in name_lower or "analyst" in name_lower:
        return factory.idea_analyst()
    elif "template" in name_lower or "selector" in name_lower:
        return factory.template_selector()
    elif "content" in name_lower or "creator" in name_lower:
        return factory.content_creator()
    elif "qa" in name_lower or "quality" in name_lower or "assurance" in name_lower:
        return factory.quality_assurance()

    return None


def list_agents() -> List[dict]:
    """
    List all available agents.

    Returns:
        List of agent information dictionaries
    """
    factory = LandingPageAgents()
    agents = []

    for agent_key, agent_name in AGENTS.items():
        agent = get_agent_by_name(agent_key)
        if agent:
            agents.append({
                "key": agent_key,
                "name": agent_name,
                "role": agent.role,
                "goal": agent.goal
            })

    return agents