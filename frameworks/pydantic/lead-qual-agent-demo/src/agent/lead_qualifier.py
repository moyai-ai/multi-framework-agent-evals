"""Lead Qualification Agent using Pydantic AI."""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from pydantic_ai import Agent

from .models import (
    Lead,
    QualificationAnalysis,
    QualificationScore,
    CompanyAnalysis,
    PersonAnalysis,
    CompanySize,
)
from ..tools.linkup_search import linkup_search_tool, LinkupSearchTool


class LeadQualificationAgent:
    """Agent for qualifying leads using web research and analysis."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        linkup_api_key: Optional[str] = None
    ):
        """
        Initialize the lead qualification agent.

        Args:
            model: OpenAI model to use (default: gpt-4o-mini)
            api_key: OpenAI API key (optional, will use env var if not provided)
            linkup_api_key: Linkup.so API key (optional, will use env var if not provided)
        """
        # Set up API keys
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        # Initialize the search tool
        self.search_tool = LinkupSearchTool(api_key=linkup_api_key)

        # Create the Pydantic AI agent
        self.agent = Agent(
            model=f"openai:{model}",
            system_prompt=self._get_system_prompt(),
            tools=[linkup_search_tool],
            output_type=QualificationAnalysis,
            deps_type=dict  # We'll pass deps as a dict
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the lead qualification agent."""
        return """You are an expert lead qualification specialist. Your task is to research and qualify leads
        for B2B software sales, specifically for developer tools and AI/ML platforms.

        For each lead, you need to:

        1. Research the Individual:
           - Find their LinkedIn profile and professional background
           - Determine their role, seniority, and decision-making authority
           - Assess their technical expertise and relevance to the product

        2. Research the Company:
           - Find the company website and understand their business
           - Determine company size, industry, and tech stack
           - Identify if they use Python, have engineering teams, and their AI/ML maturity

        3. Qualification Criteria:
           - Very High: Enterprise company with large engineering team, uses Python, has AI/ML initiatives, lead is decision-maker
           - High: Mid-market company with engineering team, uses Python, lead has purchasing authority
           - Medium: Growing company with technical needs, lead is influencer or technical lead
           - Low: Small company with limited technical resources, lead has no clear authority
           - Very Low: Company unlikely to need developer tools, lead is not in relevant role
           - Unqualified: No fit with product, wrong industry, or insufficient information

        4. Provide Actionable Insights:
           - Clear reasons for the qualification score
           - Specific talking points for sales outreach
           - Recommended next actions

        Use the search_linkup tool to gather information. Start with broad searches about the person and company,
        then narrow down to specific details. Always search for:
        - "[Person Name] [Company] LinkedIn"
        - "[Company Name] technology stack"
        - "[Company Name] engineering team size"
        - "[Person Name] [Title] background"

        Be thorough but efficient. Focus on finding the most relevant information for qualification."""

    async def qualify_lead(
        self,
        lead: Lead,
        context: Optional[Dict[str, Any]] = None
    ) -> QualificationAnalysis:
        """
        Qualify a single lead.

        Args:
            lead: Lead object to qualify
            context: Optional context dictionary with additional information

        Returns:
            QualificationAnalysis object with complete qualification details
        """
        # Generate a unique lead ID if not provided
        lead_id = str(uuid.uuid4())

        # Prepare the deps for the agent
        agent_deps = {
            "search_tool": self.search_tool,
            "lead_id": lead_id,
            **(context or {})
        }

        # Create the prompt for the agent
        prompt = f"""Please qualify the following lead:

        Name: {lead.name}
        Email: {lead.email}
        Company: {lead.company or "Unknown"}
        Title: {lead.title or "Unknown"}
        LinkedIn: {lead.linkedin_url or "Not provided"}
        Additional Info: {lead.additional_info if lead.additional_info else "None"}

        Research this lead thoroughly using web search and provide a complete qualification analysis.
        Focus on understanding both the individual's role and authority, as well as the company's
        potential need for developer tools and AI/ML platforms."""

        # Run the agent
        result = await self.agent.run(prompt, deps=agent_deps)

        # Access the data from the result
        qualification = result.data

        # Set the lead_id in the result
        if qualification:
            qualification.lead_id = lead_id

        return qualification

    async def qualify_batch(
        self,
        leads: List[Lead],
        parallel: bool = True
    ) -> List[QualificationAnalysis]:
        """
        Qualify multiple leads.

        Args:
            leads: List of Lead objects to qualify
            parallel: Whether to process leads in parallel (default: True)

        Returns:
            List of QualificationAnalysis objects
        """
        if parallel:
            import asyncio
            tasks = [self.qualify_lead(lead) for lead in leads]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out any exceptions
            qualified_leads = []
            for result in results:
                if isinstance(result, QualificationAnalysis):
                    qualified_leads.append(result)
                else:
                    print(f"Error qualifying lead: {result}")

            return qualified_leads
        else:
            qualified_leads = []
            for lead in leads:
                try:
                    analysis = await self.qualify_lead(lead)
                    qualified_leads.append(analysis)
                except Exception as e:
                    print(f"Error qualifying lead {lead.name}: {e}")

            return qualified_leads

    def get_high_value_leads(
        self,
        analyses: List[QualificationAnalysis],
        min_score: QualificationScore = QualificationScore.HIGH,
        min_confidence: float = 0.7
    ) -> List[QualificationAnalysis]:
        """
        Filter analyses to get high-value leads.

        Args:
            analyses: List of qualification analyses
            min_score: Minimum qualification score (default: HIGH)
            min_confidence: Minimum confidence level (default: 0.7)

        Returns:
            Filtered list of high-value lead analyses
        """
        score_order = {
            QualificationScore.VERY_HIGH: 6,
            QualificationScore.HIGH: 5,
            QualificationScore.MEDIUM: 4,
            QualificationScore.LOW: 3,
            QualificationScore.VERY_LOW: 2,
            QualificationScore.UNQUALIFIED: 1
        }

        min_score_value = score_order.get(min_score, 5)

        return [
            analysis for analysis in analyses
            if score_order.get(analysis.score, 0) >= min_score_value
            and analysis.confidence >= min_confidence
        ]

    def generate_outreach_priority_list(
        self,
        analyses: List[QualificationAnalysis]
    ) -> List[Dict[str, Any]]:
        """
        Generate a prioritized list for sales outreach.

        Args:
            analyses: List of qualification analyses

        Returns:
            Prioritized list with outreach recommendations
        """
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

        priority_list = []
        for i, analysis in enumerate(sorted_analyses, 1):
            priority_list.append({
                "priority": i,
                "lead_id": analysis.lead_id,
                "name": analysis.person_analysis.name,
                "company": analysis.company_analysis.name if analysis.company_analysis else "Unknown",
                "score": analysis.score,
                "confidence": analysis.confidence,
                "recommended_action": analysis.recommended_action,
                "key_talking_point": analysis.talking_points[0] if analysis.talking_points else "No specific talking points",
                "summary": analysis.summary
            })

        return priority_list