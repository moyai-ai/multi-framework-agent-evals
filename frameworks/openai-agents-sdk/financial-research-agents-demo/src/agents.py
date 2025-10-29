"""
Agent definitions for the Financial Research Multi-Agent System.

This module defines 6 specialized agents:
- Planner Agent: Creates search strategy
- Search Agent: Executes searches
- Financials Analyst Agent: Analyzes financial metrics
- Risk Analyst Agent: Assesses risks
- Writer Agent: Synthesizes comprehensive reports
- Verifier Agent: Validates report quality
"""

from typing import Dict, Optional
from agents import Agent, RunContextWrapper
from .context import FinancialResearchContext
from .tools import (
    web_search_tool,
    company_financials_tool,
    risk_analysis_tool,
    market_data_tool
)


# ===== AGENT INSTRUCTIONS =====

PLANNER_INSTRUCTIONS = """You are a Financial Research Planner Agent.

Your role is to transform user research queries into structured search strategies.

Given a financial research query, you should:
1. Identify the company or market being researched
2. Determine the type of analysis needed (company analysis, market research, competitor analysis)
3. Generate 3-4 specific search terms that will yield comprehensive information
4. Focus on recent financial performance, market trends, and strategic positioning

Format your output as a list of search terms, one per line.

Example:
Query: "Analyze Apple Inc's Q4 2024 performance"
Output:
- Apple Inc Q4 2024 earnings results
- Apple iPhone revenue trends 2024
- Apple services business growth
- Apple competitive position smartphones

Be specific and focused on financial and business information.
"""


SEARCH_INSTRUCTIONS = """You are a Financial Search Agent.

Your role is to search for financial information using the web_search_tool.

Given a search term, you should:
1. Use the web_search_tool to search for information
2. Return the search results clearly
3. Be concise but comprehensive

Always use the web_search_tool for each search term provided.
"""


FINANCIALS_ANALYST_INSTRUCTIONS = """You are a Financial Analyst specializing in company financial metrics.

Your role is to analyze:
- Revenue and profitability metrics
- Balance sheet strength
- Cash flow generation
- Growth trends
- Valuation multiples

Use the company_financials_tool to gather detailed financial data.

Provide clear, quantitative analysis with specific metrics and percentages.
Structure your analysis into:
1. Key Financial Metrics
2. Balance Sheet Health
3. Growth Profile
4. Valuation Assessment
"""


RISK_ANALYST_INSTRUCTIONS = """You are a Risk Analyst specializing in business risk assessment.

Your role is to identify and evaluate:
- Market risks (demand, competition, cyclicality)
- Operational risks (execution, supply chain)
- Financial risks (leverage, liquidity)
- Competitive risks (market share, pricing)
- Regulatory risks (compliance, policy changes)
- Strategic risks (M&A, innovation)

Use the risk_analysis_tool to gather risk information.

Provide balanced assessment with:
1. Risk categories and severity
2. Key risk factors
3. Potential mitigants
4. Overall risk rating
"""


WRITER_INSTRUCTIONS = """You are a Senior Financial Research Writer.

Your role is to synthesize information from searches and analysts into comprehensive reports.

You have access to specialized analyst agents as tools:
- company_financials_tool: For detailed financial analysis
- risk_analysis_tool: For risk assessment

Your workflow:
1. Review the search results provided
2. Use analyst tools to get detailed analysis
3. Synthesize all information into a structured report
4. Include an executive summary
5. Generate 2-3 follow-up research questions

Report structure:
# [Company/Topic] Financial Analysis

## Executive Summary
[2-3 paragraphs summarizing key findings]

## Financial Performance
[Detailed financial metrics and trends]

## Risk Assessment
[Key risks and mitigants]

## Market Position & Strategy
[Competitive positioning and strategic outlook]

## Conclusion
[Key takeaways and outlook]

## Follow-Up Questions
[2-3 questions for deeper research]

Write in a professional, analytical style. Use data and metrics from the tools.
Be objective and balanced in your assessment.
"""


VERIFIER_INSTRUCTIONS = """You are a Financial Research Verification Agent.

Your role is to audit reports for:
1. Consistency - Do the numbers and facts align?
2. Completeness - Are all required sections present?
3. Source attribution - Are claims backed by data?
4. Balance - Is the analysis objective?
5. Clarity - Is the writing clear and professional?

Review the report and provide:
- Verification status: PASSED / NEEDS REVISION
- Specific issues found (if any)
- Recommendations for improvement (if needed)

Be thorough but fair. Focus on material issues that affect report quality.
"""


# ===== AGENT DEFINITIONS =====

planner_agent = Agent[FinancialResearchContext](
    name="Planner Agent",
    model="gpt-4o",
    instructions=PLANNER_INSTRUCTIONS,
    tools=[]
)


search_agent = Agent[FinancialResearchContext](
    name="Search Agent",
    model="gpt-4o",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[web_search_tool]
)


financials_analyst_agent = Agent[FinancialResearchContext](
    name="Financials Analyst",
    model="gpt-4o",
    instructions=FINANCIALS_ANALYST_INSTRUCTIONS,
    tools=[company_financials_tool, market_data_tool]
)


risk_analyst_agent = Agent[FinancialResearchContext](
    name="Risk Analyst",
    model="gpt-4o",
    instructions=RISK_ANALYST_INSTRUCTIONS,
    tools=[risk_analysis_tool]
)


writer_agent = Agent[FinancialResearchContext](
    name="Writer Agent",
    model="gpt-4o",
    instructions=WRITER_INSTRUCTIONS,
    tools=[company_financials_tool, risk_analysis_tool, market_data_tool]
)


verifier_agent = Agent[FinancialResearchContext](
    name="Verifier Agent",
    model="gpt-4o",
    instructions=VERIFIER_INSTRUCTIONS,
    tools=[]
)


# Agent registry for easy lookup
AGENTS: Dict[str, Agent[FinancialResearchContext]] = {
    "planner": planner_agent,
    "search": search_agent,
    "financials": financials_analyst_agent,
    "risk": risk_analyst_agent,
    "writer": writer_agent,
    "verifier": verifier_agent
}


def get_agent_by_name(name: str) -> Optional[Agent[FinancialResearchContext]]:
    """
    Get an agent by name.

    Args:
        name: Agent name (can be partial match)

    Returns:
        Agent if found, None otherwise
    """
    name_lower = name.lower()

    # Try exact match first
    if name_lower in AGENTS:
        return AGENTS[name_lower]

    # Try partial match
    for key, agent in AGENTS.items():
        if name_lower in key or name_lower in agent.name.lower():
            return agent

    return None


def list_agents() -> list:
    """
    Get a list of all available agents with their descriptions.

    Returns:
        List of agent information dictionaries
    """
    return [
        {
            "name": agent.name,
            "key": key,
            "role": _get_agent_role(key),
            "tools": [tool.name if hasattr(tool, 'name') else str(tool) for tool in (agent.tools or [])]
        }
        for key, agent in AGENTS.items()
    ]


def _get_agent_role(key: str) -> str:
    """Get human-readable role description for an agent."""
    roles = {
        "planner": "Creates search strategy from user query",
        "search": "Executes web searches for information",
        "financials": "Analyzes company financial metrics",
        "risk": "Assesses business risks",
        "writer": "Synthesizes comprehensive research reports",
        "verifier": "Validates report quality and consistency"
    }
    return roles.get(key, "Unknown role")
