"""Agent definitions for the Meta Quest Knowledge Agent."""

import os
from typing import Dict, List, Optional

from crewai import Agent

from src.tools import META_QUEST_TOOLS


class MetaQuestAgents:
    """Factory class for creating Meta Quest knowledge agents."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        verbose: bool = True,
    ):
        self.model_name = model_name or os.getenv("MODEL_NAME", "gpt-4o")
        self.temperature = temperature
        self.verbose = verbose

    def knowledge_expert(self) -> Agent:
        """
        Create a Meta Quest Knowledge Expert agent.

        This agent specializes in answering questions about Meta Quest
        by searching through PDF documentation and providing accurate,
        well-sourced information.
        """
        return Agent(
            role="Meta Quest Knowledge Expert",
            goal="Provide accurate and comprehensive information about Meta Quest based on official documentation",
            backstory=(
                "You are an expert on Meta Quest VR headsets with deep knowledge of their "
                "features, setup, usage, and troubleshooting. You have access to official "
                "Meta Quest documentation and can search through it to find accurate answers "
                "to user questions. You always cite specific information from the documentation "
                "and provide clear, helpful explanations. When you don't find information in "
                "the documentation, you clearly state that rather than making assumptions."
            ),
            tools=META_QUEST_TOOLS,
            allow_delegation=False,
            verbose=self.verbose,
            llm=self.model_name,
            max_iter=10,
        )

    def technical_support(self) -> Agent:
        """
        Create a Meta Quest Technical Support agent.

        This agent focuses on troubleshooting and technical guidance
        for Meta Quest users.
        """
        return Agent(
            role="Meta Quest Technical Support Specialist",
            goal="Help users troubleshoot issues and understand technical aspects of Meta Quest",
            backstory=(
                "You are a technical support specialist with extensive experience helping "
                "Meta Quest users. You excel at breaking down complex technical information "
                "into easy-to-understand steps. You have access to Meta Quest documentation "
                "and can search for specific technical details, setup instructions, and "
                "troubleshooting guides. You always provide step-by-step guidance and ensure "
                "users understand the solutions to their problems."
            ),
            tools=META_QUEST_TOOLS,
            allow_delegation=False,
            verbose=self.verbose,
            llm=self.model_name,
            max_iter=10,
        )


# Agent registry for lookup
_agents_instance: Optional[MetaQuestAgents] = None


def get_agents_instance() -> MetaQuestAgents:
    """Get or create the global agents instance."""
    global _agents_instance
    if _agents_instance is None:
        _agents_instance = MetaQuestAgents()
    return _agents_instance


def get_agent_registry() -> Dict[str, Agent]:
    """Get the registry of all available agents."""
    agents_factory = get_agents_instance()
    return {
        "knowledge_expert": agents_factory.knowledge_expert(),
        "technical_support": agents_factory.technical_support(),
    }


def get_agent_by_name(name: str) -> Optional[Agent]:
    """
    Get an agent by name with fuzzy matching.

    Args:
        name: The agent name (supports partial matches)

    Returns:
        The matching agent or None if not found
    """
    registry = get_agent_registry()

    # Exact match
    if name in registry:
        return registry[name]

    # Partial match
    name_lower = name.lower()
    for agent_name, agent in registry.items():
        if name_lower in agent_name.lower():
            return agent

    return None


def get_initial_agent() -> Agent:
    """Get the default starting agent (knowledge expert)."""
    return get_agent_registry()["knowledge_expert"]


def list_agents() -> List[Dict[str, str]]:
    """
    List all available agents with their metadata.

    Returns:
        List of agent information dictionaries
    """
    registry = get_agent_registry()
    agents_info = []

    for name, agent in registry.items():
        agents_info.append(
            {
                "name": name,
                "role": agent.role,
                "goal": agent.goal,
                "tools": [tool.name for tool in agent.tools] if agent.tools else [],
            }
        )

    return agents_info


# Export the main registry
AGENTS = get_agent_registry()
