"""Task definitions for the Meta Quest Knowledge Agent."""

from crewai import Task
from crewai import Agent


class MetaQuestTasks:
    """Factory class for creating Meta Quest knowledge tasks."""

    @staticmethod
    def answer_question_task(agent: Agent, question: str) -> Task:
        """
        Create a task to answer a question about Meta Quest.

        Args:
            agent: The agent to assign the task to
            question: The user's question about Meta Quest

        Returns:
            A Task configured to answer the question
        """
        return Task(
            description=(
                f"Answer the following question about Meta Quest: {question}\n\n"
                "Search the Meta Quest documentation thoroughly to find accurate information. "
                "Provide a comprehensive answer that includes:\n"
                "1. Direct answer to the question\n"
                "2. Relevant details and context from the documentation\n"
                "3. Any important related information the user should know\n\n"
                "If the documentation doesn't contain information to answer the question, "
                "clearly state that and explain what information is not available."
            ),
            expected_output=(
                "A well-structured answer that:\n"
                "- Directly addresses the user's question\n"
                "- Includes specific information from Meta Quest documentation\n"
                "- Provides helpful context and details\n"
                "- Is clear, accurate, and easy to understand"
            ),
            agent=agent,
        )

    @staticmethod
    def multi_question_task(agent: Agent, questions: list[str]) -> Task:
        """
        Create a task to answer multiple related questions.

        Args:
            agent: The agent to assign the task to
            questions: List of questions about Meta Quest

        Returns:
            A Task configured to answer all questions
        """
        questions_formatted = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

        return Task(
            description=(
                f"Answer the following questions about Meta Quest:\n\n{questions_formatted}\n\n"
                "For each question:\n"
                "1. Search the Meta Quest documentation for accurate information\n"
                "2. Provide a clear and comprehensive answer\n"
                "3. Include relevant details and context\n\n"
                "Organize your response so each question is clearly addressed separately."
            ),
            expected_output=(
                "A well-organized response that answers each question:\n"
                "- Clearly labeled answers for each question\n"
                "- Accurate information from the documentation\n"
                "- Helpful context and details\n"
                "- Professional and easy to understand"
            ),
            agent=agent,
        )

    @staticmethod
    def technical_support_task(agent: Agent, issue: str) -> Task:
        """
        Create a task to provide technical support.

        Args:
            agent: The agent to assign the task to
            issue: The technical issue or question

        Returns:
            A Task configured to provide technical support
        """
        return Task(
            description=(
                f"Provide technical support for the following Meta Quest issue or question: {issue}\n\n"
                "Search the documentation for relevant troubleshooting steps, setup instructions, "
                "or technical information. Provide:\n"
                "1. A clear explanation of the issue or answer to the question\n"
                "2. Step-by-step guidance or instructions if applicable\n"
                "3. Any important warnings or tips\n"
                "4. Additional resources or related information"
            ),
            expected_output=(
                "Technical support response that includes:\n"
                "- Clear explanation or solution\n"
                "- Step-by-step instructions if needed\n"
                "- Relevant warnings or best practices\n"
                "- Easy to follow and actionable"
            ),
            agent=agent,
        )

    @staticmethod
    def research_topic_task(agent: Agent, topic: str) -> Task:
        """
        Create a task to research a specific topic in depth.

        Args:
            agent: The agent to assign the task to
            topic: The topic to research

        Returns:
            A Task configured to research the topic
        """
        return Task(
            description=(
                f"Research the following topic about Meta Quest: {topic}\n\n"
                "Search the documentation comprehensively and provide:\n"
                "1. Overview of the topic\n"
                "2. Key features and capabilities\n"
                "3. Important details and specifications\n"
                "4. Use cases or examples\n"
                "5. Any limitations or considerations\n\n"
                "Be thorough and include all relevant information from the documentation."
            ),
            expected_output=(
                "Comprehensive research report that includes:\n"
                "- Clear overview and introduction\n"
                "- Detailed information organized in sections\n"
                "- Specific facts and details from documentation\n"
                "- Well-structured and informative"
            ),
            agent=agent,
        )
