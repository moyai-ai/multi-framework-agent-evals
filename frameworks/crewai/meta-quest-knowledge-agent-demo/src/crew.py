"""Crew orchestration for the Meta Quest Knowledge Agent."""

import os
from typing import Dict, Any, List

from crewai import Crew, Process
from dotenv import load_dotenv

from src.agents import MetaQuestAgents
from src.tasks import MetaQuestTasks


# Load environment variables
load_dotenv()


class MetaQuestCrew:
    """Orchestrates the Meta Quest knowledge crew."""

    def __init__(
        self,
        model_name: str = None,
        temperature: float = None,
        verbose: bool = True,
    ):
        self.model_name = model_name or os.getenv("MODEL_NAME", "gpt-4o")
        # Use passed temperature if provided, otherwise use env var, otherwise default
        if temperature is not None:
            self.temperature = temperature
        else:
            env_temp = os.getenv("TEMPERATURE")
            self.temperature = float(env_temp) if env_temp else 0.7
        self.verbose = os.getenv("CREW_VERBOSE", str(verbose)).lower() == "true"
        self.max_iterations = int(os.getenv("MAX_ITERATIONS", "10"))

        # Initialize agents
        self.agents_factory = MetaQuestAgents(
            model_name=self.model_name,
            temperature=self.temperature,
            verbose=self.verbose,
        )
        self.tasks_factory = MetaQuestTasks()

    def answer_question(self, question: str, use_technical_support: bool = False) -> str:
        """
        Answer a question about Meta Quest.

        Args:
            question: The user's question
            use_technical_support: Whether to use the technical support agent

        Returns:
            The crew's answer to the question
        """
        # Select appropriate agent
        if use_technical_support:
            agent = self.agents_factory.technical_support()
            task = self.tasks_factory.technical_support_task(agent, question)
        else:
            agent = self.agents_factory.knowledge_expert()
            task = self.tasks_factory.answer_question_task(agent, question)

        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose,
        )

        # Execute
        result = crew.kickoff()
        return str(result)

    def answer_multiple_questions(self, questions: List[str]) -> str:
        """
        Answer multiple questions about Meta Quest.

        Args:
            questions: List of user questions

        Returns:
            The crew's answers to all questions
        """
        agent = self.agents_factory.knowledge_expert()
        task = self.tasks_factory.multi_question_task(agent, questions)

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose,
        )

        result = crew.kickoff()
        return str(result)

    def research_topic(self, topic: str) -> str:
        """
        Research a specific topic about Meta Quest.

        Args:
            topic: The topic to research

        Returns:
            The crew's research findings
        """
        agent = self.agents_factory.knowledge_expert()
        task = self.tasks_factory.research_topic_task(agent, topic)

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.verbose,
        )

        result = crew.kickoff()
        return str(result)

    def run_conversation(self, conversation: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Run a multi-turn conversation.

        Args:
            conversation: List of conversation turns with 'user' messages

        Returns:
            List of conversation turns with 'assistant' responses added
        """
        results = []
        agent = self.agents_factory.knowledge_expert()

        for turn in conversation:
            user_message = turn.get("user", "")
            if not user_message:
                continue

            # Create task for this turn
            task = self.tasks_factory.answer_question_task(agent, user_message)

            # Create crew
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=self.verbose,
            )

            # Execute
            result = crew.kickoff()

            results.append(
                {
                    "user": user_message,
                    "assistant": str(result),
                    "agent": "knowledge_expert",
                }
            )

        return results


def create_crew(
    model_name: str = None,
    temperature: float = None,
    verbose: bool = True,
) -> MetaQuestCrew:
    """
    Factory function to create a Meta Quest crew.

    Args:
        model_name: LLM model name
        temperature: LLM temperature
        verbose: Whether to enable verbose output

    Returns:
        Configured MetaQuestCrew instance
    """
    return MetaQuestCrew(
        model_name=model_name,
        temperature=temperature,
        verbose=verbose,
    )
