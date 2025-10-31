"""
Research Agents

Defines specialized agents for different phases of the research workflow.
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import BaseTool
from langchain.agents import create_agent as create_react_agent

from src.context import (
    ResearchContext,
    WorkflowStage,
    SearchPlan,
    SearchResult,
    AnalysisFindings,
    ReportSection,
    VerificationResult,
)
from src.tools import (
    web_search_tool,
    summary_tool,
    analysis_tool,
    verification_tool,
    concurrent_search_tool,
)


# Model configuration from environment
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4")
PLANNER_MODEL = os.getenv("PLANNER_MODEL", DEFAULT_MODEL)
SEARCH_MODEL = os.getenv("SEARCH_MODEL", DEFAULT_MODEL)
ANALYST_MODEL = os.getenv("ANALYST_MODEL", DEFAULT_MODEL)
SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", DEFAULT_MODEL)
WRITER_MODEL = os.getenv("WRITER_MODEL", DEFAULT_MODEL)
VERIFIER_MODEL = os.getenv("VERIFIER_MODEL", DEFAULT_MODEL)


class ResearchAgent:
    """Base class for research agents."""

    def __init__(self, name: str, model_name: str, tools: List[BaseTool], system_prompt: str):
        """
        Initialize a research agent.

        Args:
            name: Name of the agent
            model_name: Name of the LLM model to use
            tools: List of tools available to the agent
            system_prompt: System prompt defining the agent's role
        """
        self.name = name
        self.model_name = model_name
        self.tools = tools
        self.system_prompt = system_prompt

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.7,
            max_retries=2,
        )

        # Create agent with langchain
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            system_prompt=system_prompt,
        )

    async def execute(self, context: ResearchContext, input_text: str) -> Dict[str, Any]:
        """
        Execute the agent with given context and input.

        Args:
            context: Research context
            input_text: Input text for the agent

        Returns:
            Agent execution results
        """
        try:
            messages = [HumanMessage(content=input_text)]
            result = await self.agent.ainvoke({"messages": messages})

            # Extract the agent's response from the result
            if "messages" in result and result["messages"]:
                output = result["messages"][-1].content if result["messages"] else ""
            else:
                output = str(result)

            return {
                "success": True,
                "output": output,
                "intermediate_steps": [],
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": "",
            }


class PlannerAgent(ResearchAgent):
    """Agent responsible for creating search plans."""

    def __init__(self):
        system_prompt = """You are a Research Planner specializing in creating comprehensive search strategies.

Your responsibilities:
1. Analyze the user's research query and identify key concepts
2. Generate 3-5 diverse search terms that will gather comprehensive information
3. Consider different angles and perspectives on the topic
4. Ensure search terms are specific enough to yield relevant results
5. Create a clear search strategy explanation

When creating a search plan:
- Break down complex topics into searchable components
- Include both broad and specific search terms
- Consider technical terms, synonyms, and related concepts
- Think about different aspects: current state, history, future trends, controversies
- Prioritize search terms by expected relevance

Output format:
- Provide a list of search terms (3-5 terms)
- Include a brief strategy explanation
- Suggest the order in which searches should be conducted"""

        super().__init__(
            name="PlannerAgent",
            model_name=PLANNER_MODEL,
            tools=[],  # Planner doesn't need tools
            system_prompt=system_prompt,
        )

    async def create_search_plan(self, context: ResearchContext) -> SearchPlan:
        """
        Create a search plan based on the research query.

        Args:
            context: Research context with the query

        Returns:
            SearchPlan with search terms and strategy
        """
        input_text = f"""Create a comprehensive search plan for the following research query:

Query: {context.query}
Research Type: {context.research_type.value}

Please provide:
1. 3-5 specific search terms
2. A clear search strategy
3. Expected information from each search term"""

        result = await self.execute(context, input_text)

        if result["success"]:
            # Parse the output to extract search terms
            # In production, this would use structured output
            output = result["output"]
            search_terms = self._extract_search_terms(output)
            strategy = self._extract_strategy(output)

            return SearchPlan(
                search_terms=search_terms,
                search_strategy=strategy,
                max_results_per_term=5,
            )
        else:
            # Fallback search plan
            return SearchPlan(
                search_terms=[context.query, f"{context.query} research", f"{context.query} analysis"],
                search_strategy="Basic search strategy due to planning error",
                max_results_per_term=5,
            )

    def _extract_search_terms(self, output: str) -> List[str]:
        """Extract search terms from agent output."""
        # Simple extraction logic - in production, use structured output
        terms = []
        lines = output.split("\n")
        for line in lines:
            if any(marker in line for marker in ["1.", "2.", "3.", "4.", "5.", "-", "*"]):
                # Clean and extract term
                term = line.strip().lstrip("0123456789.-* ").strip()
                if term and len(term) > 3 and not term.startswith("Strategy"):
                    terms.append(term)
        return terms[:5] if terms else ["default search"]

    def _extract_strategy(self, output: str) -> str:
        """Extract strategy from agent output."""
        if "strategy" in output.lower():
            parts = output.lower().split("strategy")
            if len(parts) > 1:
                return parts[1].split("\n")[0].strip()
        return "Comprehensive search across multiple dimensions"


class SearchAgent(ResearchAgent):
    """Agent responsible for executing searches."""

    def __init__(self):
        system_prompt = """You are a Research Search Specialist with expertise in finding relevant information.

Your responsibilities:
1. Execute web searches efficiently
2. Evaluate search result relevance
3. Collect comprehensive information
4. Filter out low-quality or duplicate content
5. Organize results by relevance and quality

When conducting searches:
- Use the provided search tools effectively
- Prioritize authoritative and recent sources
- Gather diverse perspectives on the topic
- Ensure sufficient coverage of the search query
- Track source credibility

Focus on finding:
- Primary sources and authoritative content
- Recent and up-to-date information
- Diverse viewpoints and comprehensive coverage
- Supporting evidence and data"""

        super().__init__(
            name="SearchAgent",
            model_name=SEARCH_MODEL,
            tools=[web_search_tool, concurrent_search_tool],
            system_prompt=system_prompt,
        )

    async def conduct_searches(self, context: ResearchContext) -> Dict[str, List[SearchResult]]:
        """
        Conduct searches based on the search plan.

        Args:
            context: Research context with search plan

        Returns:
            Dictionary mapping search terms to results
        """
        if not context.search_plan:
            return {}

        search_terms = context.search_plan.search_terms[:3]  # Limit to 3 concurrent searches
        input_text = f"""Conduct searches for the following terms and collect relevant results:

Search Terms: {', '.join(search_terms)}
Research Topic: {context.query}

Use the concurrent_search_tool to search all terms simultaneously.
Collect up to {context.search_plan.max_results_per_term} results per term."""

        result = await self.execute(context, input_text)

        if result["success"]:
            # Process search results from intermediate steps
            search_results = {}
            for term in search_terms:
                search_results[term] = []

            # Extract results from tool calls in intermediate steps
            for step in result.get("intermediate_steps", []):
                if len(step) >= 2 and hasattr(step[0], "tool"):
                    if step[0].tool in ["web_search_tool", "concurrent_search_tool"]:
                        tool_output = step[1]
                        if isinstance(tool_output, dict):
                            for term, results in tool_output.items():
                                if term in search_results:
                                    for r in results:
                                        search_results[term].append(SearchResult(
                                            url=r.get("url", ""),
                                            title=r.get("title", ""),
                                            snippet=r.get("snippet", ""),
                                            content=r.get("content"),
                                            relevance_score=r.get("relevance_score", 0.0),
                                        ))

            return search_results
        else:
            return {}


class AnalystAgent(ResearchAgent):
    """Agent responsible for analyzing search results."""

    def __init__(self):
        system_prompt = """You are a Research Analyst specializing in extracting insights from information.

Your responsibilities:
1. Analyze collected search results thoroughly
2. Identify key insights and patterns
3. Find supporting evidence for claims
4. Detect contradictions or conflicting information
5. Identify knowledge gaps that need addressing

When analyzing:
- Synthesize information from multiple sources
- Identify trends and patterns
- Evaluate the strength of evidence
- Note areas of consensus and disagreement
- Assess information quality and reliability

Focus on:
- Key findings and takeaways
- Supporting data and evidence
- Contradictions and uncertainties
- Gaps in available information
- Confidence levels for different insights"""

        super().__init__(
            name="AnalystAgent",
            model_name=ANALYST_MODEL,
            tools=[analysis_tool],
            system_prompt=system_prompt,
        )

    async def analyze_results(self, context: ResearchContext) -> AnalysisFindings:
        """
        Analyze search results and extract insights.

        Args:
            context: Research context with search results

        Returns:
            AnalysisFindings with insights and evidence
        """
        all_results = context.get_all_search_results()

        if not all_results:
            return AnalysisFindings(confidence_level=0.0)

        # Prepare content for analysis
        content_pieces = []
        for result in all_results[:10]:  # Analyze top 10 results
            content_pieces.append(f"Source: {result.title}\n{result.content or result.snippet}")

        combined_content = "\n\n".join(content_pieces)

        input_text = f"""Analyze the following search results for the research query: {context.query}

Content to analyze:
{combined_content[:3000]}  # Limit content length

Please identify:
1. Key insights and findings
2. Supporting evidence
3. Any contradictions
4. Knowledge gaps
5. Overall confidence level"""

        result = await self.execute(context, input_text)

        if result["success"]:
            # Parse analysis results
            output = result["output"]
            return AnalysisFindings(
                key_insights=self._extract_insights(output),
                supporting_evidence=self._extract_evidence(output),
                contradictions=self._extract_contradictions(output),
                gaps=self._extract_gaps(output),
                confidence_level=0.75,  # Default confidence
            )
        else:
            return AnalysisFindings(confidence_level=0.0)

    def _extract_insights(self, output: str) -> List[str]:
        """Extract key insights from analysis output."""
        insights = []
        if "insight" in output.lower() or "finding" in output.lower():
            lines = output.split("\n")
            for line in lines:
                if any(keyword in line.lower() for keyword in ["insight", "finding", "key", "important"]):
                    cleaned = line.strip().lstrip("0123456789.-* ").strip()
                    if cleaned and len(cleaned) > 10:
                        insights.append(cleaned)
        return insights[:5]

    def _extract_evidence(self, output: str) -> List[Dict[str, Any]]:
        """Extract supporting evidence."""
        # Simplified extraction
        return [{"type": "analysis", "content": "Evidence extracted from search results"}]

    def _extract_contradictions(self, output: str) -> List[str]:
        """Extract contradictions."""
        contradictions = []
        if "contradict" in output.lower() or "conflict" in output.lower():
            lines = output.split("\n")
            for line in lines:
                if "contradict" in line.lower() or "conflict" in line.lower():
                    contradictions.append(line.strip())
        return contradictions[:3]

    def _extract_gaps(self, output: str) -> List[str]:
        """Extract knowledge gaps."""
        gaps = []
        if "gap" in output.lower() or "missing" in output.lower():
            lines = output.split("\n")
            for line in lines:
                if "gap" in line.lower() or "missing" in line.lower():
                    gaps.append(line.strip())
        return gaps[:3]


class SummarizerAgent(ResearchAgent):
    """Agent responsible for summarizing information."""

    def __init__(self):
        system_prompt = """You are a Research Summarizer specializing in creating concise, informative summaries.

Your responsibilities:
1. Condense large amounts of information
2. Preserve key points and insights
3. Maintain accuracy while reducing volume
4. Create hierarchical summaries (executive, detailed)
5. Ensure readability and clarity

When summarizing:
- Focus on the most important information
- Maintain logical flow and structure
- Preserve critical details and data
- Remove redundancy and repetition
- Use clear, concise language

Create summaries that are:
- Accurate and faithful to source material
- Well-structured and easy to read
- Appropriately detailed for the audience
- Focused on answering the research query"""

        super().__init__(
            name="SummarizerAgent",
            model_name=SUMMARIZER_MODEL,
            tools=[summary_tool],
            system_prompt=system_prompt,
        )

    async def create_summaries(self, context: ResearchContext) -> List[str]:
        """
        Create summaries of the research findings.

        Args:
            context: Research context with analysis

        Returns:
            List of summaries at different levels
        """
        if not context.analysis_findings:
            return []

        # Prepare content for summarization
        content_parts = []

        # Add insights
        if context.analysis_findings.key_insights:
            content_parts.append("Key Insights:\n" + "\n".join(context.analysis_findings.key_insights))

        # Add search results summary
        all_results = context.get_all_search_results()
        if all_results:
            content_parts.append("\nInformation gathered:")
            for result in all_results[:5]:
                content_parts.append(f"- {result.title}: {result.snippet}")

        combined_content = "\n".join(content_parts)

        input_text = f"""Create comprehensive summaries for the research query: {context.query}

Content to summarize:
{combined_content[:2000]}

Please create:
1. An executive summary (2-3 sentences)
2. A detailed summary (1-2 paragraphs)
3. Key takeaways (3-5 bullet points)"""

        result = await self.execute(context, input_text)

        if result["success"]:
            return [result["output"]]
        else:
            return ["Summary generation failed"]


class WriterAgent(ResearchAgent):
    """Agent responsible for writing the final research report."""

    def __init__(self):
        system_prompt = """You are a Research Report Writer specializing in creating comprehensive research documents.

Your responsibilities:
1. Synthesize all research findings into a cohesive report
2. Create well-structured, professional documentation
3. Include all relevant sections and supporting evidence
4. Ensure clarity and readability
5. Maintain academic/professional standards

Report structure should include:
- Executive Summary
- Introduction and Background
- Research Methodology
- Key Findings
- Detailed Analysis
- Conclusions
- Recommendations (if applicable)
- References

Writing guidelines:
- Use clear, professional language
- Maintain logical flow between sections
- Support claims with evidence
- Acknowledge limitations and uncertainties
- Provide actionable insights where relevant"""

        super().__init__(
            name="WriterAgent",
            model_name=WRITER_MODEL,
            tools=[],  # Writer uses synthesized information
            system_prompt=system_prompt,
        )

    async def write_report(self, context: ResearchContext) -> str:
        """
        Write the final research report.

        Args:
            context: Complete research context

        Returns:
            Final research report as formatted text
        """
        # Gather all information for the report
        sections = []

        # Executive Summary
        if context.raw_summaries:
            sections.append(f"## Executive Summary\n\n{context.raw_summaries[0]}\n")

        # Introduction
        sections.append(f"## Introduction\n\nThis report presents research findings for: {context.query}\n")

        # Methodology
        if context.search_plan:
            sections.append(f"## Research Methodology\n\nSearch Strategy: {context.search_plan.search_strategy}\n")
            sections.append(f"Search Terms Used: {', '.join(context.search_plan.search_terms)}\n")

        # Key Findings
        if context.analysis_findings and context.analysis_findings.key_insights:
            sections.append("## Key Findings\n")
            for insight in context.analysis_findings.key_insights:
                sections.append(f"- {insight}")
            sections.append("\n")

        # Detailed Analysis
        sections.append("## Detailed Analysis\n")
        if context.analysis_findings:
            sections.append(f"Confidence Level: {context.analysis_findings.confidence_level:.2%}\n")
            if context.analysis_findings.contradictions:
                sections.append("\n### Contradictions and Uncertainties\n")
                for contradiction in context.analysis_findings.contradictions:
                    sections.append(f"- {contradiction}")

            if context.analysis_findings.gaps:
                sections.append("\n### Knowledge Gaps\n")
                for gap in context.analysis_findings.gaps:
                    sections.append(f"- {gap}")

        # Sources
        all_results = context.get_all_search_results()
        if all_results:
            sections.append("\n## Sources\n")
            for i, result in enumerate(all_results[:10], 1):
                sections.append(f"{i}. [{result.title}]({result.url})")

        # Combine all sections
        report = "\n".join(sections)

        input_text = f"""Please review and enhance the following research report:

{report[:3000]}

Ensure the report is:
- Well-structured and professional
- Clear and comprehensive
- Properly formatted
- Ready for presentation"""

        result = await self.execute(context, input_text)

        if result["success"]:
            return result["output"]
        else:
            return report  # Return original if enhancement fails


class VerifierAgent(ResearchAgent):
    """Agent responsible for verifying research quality."""

    def __init__(self):
        system_prompt = """You are a Research Quality Verifier specializing in validating research outputs.

Your responsibilities:
1. Verify accuracy of research findings
2. Check completeness of the research
3. Validate consistency across the report
4. Identify potential issues or biases
5. Suggest improvements if needed

Verification criteria:
- Accuracy: Are claims supported by evidence?
- Completeness: Are all aspects of the query addressed?
- Consistency: Is information consistent throughout?
- Reliability: Are sources credible?
- Clarity: Is the report clear and well-structured?

When verifying:
- Check factual accuracy where possible
- Ensure logical consistency
- Verify source credibility
- Identify unsupported claims
- Note any biases or limitations

Provide:
- Verification scores for each criterion
- List of issues found
- Suggestions for improvement
- Overall quality assessment"""

        super().__init__(
            name="VerifierAgent",
            model_name=VERIFIER_MODEL,
            tools=[verification_tool],
            system_prompt=system_prompt,
        )

    async def verify_research(self, context: ResearchContext) -> VerificationResult:
        """
        Verify the quality of the research.

        Args:
            context: Complete research context with report

        Returns:
            VerificationResult with quality metrics
        """
        input_text = f"""Please verify the following research report:

Query: {context.query}
Report Length: {len(context.full_report)} characters
Number of Sources: {context.total_results_collected}
Key Insights Found: {len(context.analysis_findings.key_insights) if context.analysis_findings else 0}

Report Summary:
{context.executive_summary}

Please evaluate:
1. Accuracy of information
2. Completeness of coverage
3. Consistency of findings
4. Overall quality"""

        result = await self.execute(context, input_text)

        if result["success"]:
            # Parse verification results
            output = result["output"]
            return VerificationResult(
                is_verified=True,
                accuracy_score=0.85,  # Default scores
                completeness_score=0.80,
                consistency_score=0.90,
                issues_found=self._extract_issues(output),
                suggestions=self._extract_suggestions(output),
            )
        else:
            return VerificationResult(is_verified=False)

    def _extract_issues(self, output: str) -> List[str]:
        """Extract issues from verification output."""
        issues = []
        if "issue" in output.lower() or "problem" in output.lower():
            lines = output.split("\n")
            for line in lines:
                if "issue" in line.lower() or "problem" in line.lower():
                    issues.append(line.strip())
        return issues[:5]

    def _extract_suggestions(self, output: str) -> List[str]:
        """Extract suggestions from verification output."""
        suggestions = []
        if "suggest" in output.lower() or "recommend" in output.lower():
            lines = output.split("\n")
            for line in lines:
                if "suggest" in line.lower() or "recommend" in line.lower():
                    suggestions.append(line.strip())
        return suggestions[:5]


# Agent Registry
AGENTS: Dict[str, ResearchAgent] = {
    "planner": PlannerAgent(),
    "search": SearchAgent(),
    "analyst": AnalystAgent(),
    "summarizer": SummarizerAgent(),
    "writer": WriterAgent(),
    "verifier": VerifierAgent(),
}


def get_agent_by_name(name: str) -> Optional[ResearchAgent]:
    """
    Get an agent by name.

    Args:
        name: Name of the agent

    Returns:
        Agent instance if found, None otherwise
    """
    # Try exact match first
    if name in AGENTS:
        return AGENTS[name]

    # Try case-insensitive match
    name_lower = name.lower()
    for key, agent in AGENTS.items():
        if key.lower() == name_lower:
            return agent

    return None


def list_agents() -> List[str]:
    """
    List all available agents.

    Returns:
        List of agent names
    """
    return list(AGENTS.keys())