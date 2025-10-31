"""
Relational Data Agents

Defines specialized agents for different aspects of database querying and analysis.
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.context import (
    ConversationContext,
    QueryResult,
    QueryType,
    AnalysisInsight,
    QueryPlan,
    context_manager,
)
from src.tools import get_all_tools, schema_inspector_tool, sql_executor_tool, data_validator_tool, aggregation_tool, visualization_tool
from src.prompts import get_prompt_for_agent


# Model configuration from environment
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4")
SCHEMA_ANALYST_MODEL = os.getenv("SCHEMA_ANALYST_MODEL", DEFAULT_MODEL)
QUERY_BUILDER_MODEL = os.getenv("QUERY_BUILDER_MODEL", DEFAULT_MODEL)
DATA_ANALYST_MODEL = os.getenv("DATA_ANALYST_MODEL", DEFAULT_MODEL)
REPORT_WRITER_MODEL = os.getenv("REPORT_WRITER_MODEL", "gpt-3.5-turbo")


class RelationalDataAgent:
    """Base class for relational data agents."""

    def __init__(self, name: str, agent_type: str, model_name: str, tools: List[BaseTool]):
        """
        Initialize a relational data agent.

        Args:
            name: Name of the agent
            agent_type: Type of agent for prompt selection
            model_name: Name of the LLM model to use
            tools: List of tools available to the agent
        """
        self.name = name
        self.agent_type = agent_type
        self.model_name = model_name
        self.tools = tools

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.3,  # Lower temperature for more consistent SQL generation
            max_retries=2,
        )

        # Get system prompt for this agent type
        system_prompt = get_prompt_for_agent(agent_type)

        # Create agent using the new LangChain v1.0 API
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
        )

    async def execute(self, context: ConversationContext, input_text: str) -> Dict[str, Any]:
        """
        Execute the agent with given context and input.

        Args:
            context: Conversation context
            input_text: Input text for the agent

        Returns:
            Agent execution results
        """
        try:
            # Include context in the input
            enriched_input = self._enrich_input_with_context(input_text, context)

            # Execute agent with the new v1.0 API
            # The new agent returns a structured response
            result = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=enriched_input)]}
            )

            # Extract the response from the new format
            # In v1.0, the agent returns messages in the response
            output = ""
            if hasattr(result, 'messages') and result.messages:
                # Get the last AI message as the output
                for msg in reversed(result.messages):
                    if isinstance(msg, AIMessage):
                        output = msg.content
                        break
            elif isinstance(result, dict) and 'messages' in result:
                for msg in reversed(result['messages']):
                    if hasattr(msg, 'content'):
                        output = msg.content
                        break
            else:
                # Fallback: try to extract output directly
                output = str(result)

            return {
                "success": True,
                "output": output,
                "intermediate_steps": [],  # v1.0 doesn't expose intermediate steps the same way
                "agent": self.name,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
            }

    def _enrich_input_with_context(self, input_text: str, context: ConversationContext) -> str:
        """Add relevant context to the input."""
        enriched = input_text

        # Add information about previously referenced tables
        if context.tables_referenced:
            enriched += f"\n\nPreviously referenced tables: {', '.join(context.tables_referenced)}"

        # Add recent successful queries for reference
        recent_queries = context.get_successful_queries()
        if recent_queries and len(recent_queries) > 0:
            enriched += "\n\nRecent successful queries:"
            for q in recent_queries[-3:]:  # Last 3 queries
                enriched += f"\n- {q.query}"

        return enriched


class SchemaAnalystAgent(RelationalDataAgent):
    """Agent specialized in understanding database schemas."""

    def __init__(self):
        super().__init__(
            name="Schema Analyst",
            agent_type="schema_analyst",
            model_name=SCHEMA_ANALYST_MODEL,
            tools=[schema_inspector_tool],
        )

    async def analyze_schema_for_query(
        self, context: ConversationContext, request: str
    ) -> Dict[str, Any]:
        """
        Analyze the database schema to determine tables and relationships needed for a query.

        Args:
            context: Conversation context
            request: User's request

        Returns:
            Schema analysis results
        """
        analysis_prompt = f"""
        Analyze the database schema to determine:
        1. Which tables are needed for this request: {request}
        2. What relationships exist between these tables
        3. Which columns should be selected
        4. Any potential performance considerations

        Provide a clear analysis of the schema requirements.
        """

        result = await self.execute(context, analysis_prompt)

        if result["success"]:
            # Extract tables mentioned in the analysis
            output = result["output"]
            # Simple extraction - in production, use NLP
            tables = []
            for line in output.split("\n"):
                if "table" in line.lower():
                    words = line.split()
                    for word in words:
                        if word.lower() in ["customers", "orders", "products", "order_items", "inventory_logs"]:
                            if word.lower() not in tables:
                                tables.append(word.lower())

            for table in tables:
                if table not in context.tables_referenced:
                    context.tables_referenced.append(table)

        return result


class QueryBuilderAgent(RelationalDataAgent):
    """Agent specialized in building SQL queries."""

    def __init__(self):
        super().__init__(
            name="Query Builder",
            agent_type="query_builder",
            model_name=QUERY_BUILDER_MODEL,
            tools=[sql_executor_tool, data_validator_tool],
        )

    async def build_and_execute_query(
        self, context: ConversationContext, request: str, schema_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build and execute a SQL query based on the request.

        Args:
            context: Conversation context
            request: Query request
            schema_info: Optional schema information from Schema Analyst

        Returns:
            Query execution results
        """
        build_prompt = f"""
        Build a SQL query for this request: {request}

        Requirements:
        1. Generate a safe, optimized SQL query
        2. Validate the query before execution
        3. Execute the query and return results
        4. Explain what the query does

        Maximum results: {context.max_results}
        """

        if schema_info:
            build_prompt += f"\n\nSchema information:\n{schema_info}"

        result = await self.execute(context, build_prompt)

        # Track query in context
        if result["success"]:
            # Extract executed query from intermediate steps
            for step in result.get("intermediate_steps", []):
                if step[0].tool == "sql_executor_tool":
                    query = step[0].tool_input.get("query", "")
                    if query:
                        query_result = QueryResult(
                            query=query,
                            query_type=self._classify_query(query),
                            success=True,
                            timestamp=datetime.now(timezone.utc),
                        )
                        context.add_query_result(query_result)
                        break

        return result

    def _classify_query(self, query: str) -> QueryType:
        """Classify the type of query."""
        query_upper = query.upper()
        if "JOIN" in query_upper:
            return QueryType.JOIN
        elif any(agg in query_upper for agg in ["SUM", "AVG", "COUNT", "GROUP BY"]):
            return QueryType.AGGREGATION
        elif "SELECT" in query_upper and "FROM" in query_upper:
            return QueryType.SIMPLE_SELECT
        else:
            return QueryType.COMPLEX


class DataAnalystAgent(RelationalDataAgent):
    """Agent specialized in analyzing query results."""

    def __init__(self):
        super().__init__(
            name="Data Analyst",
            agent_type="data_analyst",
            model_name=DATA_ANALYST_MODEL,
            tools=[aggregation_tool, visualization_tool],
        )

    async def analyze_results(
        self, context: ConversationContext, query_results: str, original_request: str
    ) -> Dict[str, Any]:
        """
        Analyze query results and provide insights.

        Args:
            context: Conversation context
            query_results: Results from query execution
            original_request: Original user request

        Returns:
            Analysis results with insights
        """
        analysis_prompt = f"""
        Analyze these query results and provide insights:

        Original Request: {original_request}

        Query Results:
        {query_results}

        Please:
        1. Identify key patterns or trends
        2. Highlight any anomalies or interesting findings
        3. Suggest follow-up analyses if appropriate
        4. Create appropriate visualizations

        Focus on actionable insights that answer the original request.
        """

        result = await self.execute(context, analysis_prompt)

        # Create insights for context
        if result["success"]:
            insight = AnalysisInsight(
                insight_type="analysis",
                description=result["output"][:200],  # First 200 chars as summary
                supporting_data={"full_analysis": result["output"]},
                confidence=0.8,
            )
            context.add_insight(insight)

        return result


class ReportWriterAgent(RelationalDataAgent):
    """Agent specialized in creating reports from analysis."""

    def __init__(self):
        super().__init__(
            name="Report Writer",
            agent_type="report_writer",
            model_name=REPORT_WRITER_MODEL,
            tools=[visualization_tool],
        )

    async def create_report(
        self, context: ConversationContext, analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a formatted report from analysis results.

        Args:
            context: Conversation context
            analysis_results: Results from data analysis

        Returns:
            Formatted report
        """
        report_prompt = f"""
        Create a professional report based on this analysis:

        Original Request: {context.original_request}

        Analysis Results:
        {analysis_results.get('output', '')}

        Create a report that includes:
        1. Executive Summary
        2. Key Findings
        3. Data Visualization (if applicable)
        4. Recommendations
        5. Technical Details (queries used, tables accessed)

        Format the report for {context.output_format} output.
        """

        return await self.execute(context, report_prompt)


class OrchestratorAgent(RelationalDataAgent):
    """Main orchestrator agent that coordinates sub-agents."""

    def __init__(self):
        super().__init__(
            name="Orchestrator",
            agent_type="orchestrator",
            model_name=DEFAULT_MODEL,
            tools=[],  # Orchestrator doesn't use tools directly
        )

        # Initialize sub-agents
        self.schema_analyst = SchemaAnalystAgent()
        self.query_builder = QueryBuilderAgent()
        self.data_analyst = DataAnalystAgent()
        self.report_writer = ReportWriterAgent()

    async def process_request(self, request: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user request by coordinating sub-agents.

        Args:
            request: User's request
            session_id: Optional session ID for context

        Returns:
            Complete response with results and insights
        """
        # Create or get context
        if session_id:
            context = context_manager.get_context(session_id)
            if not context:
                context = context_manager.create_context(session_id, request)
        else:
            import uuid
            session_id = str(uuid.uuid4())
            context = context_manager.create_context(session_id, request)

        try:
            # Update context
            context.original_request = request
            context.current_stage = "planning"

            # Step 1: Analyze schema requirements
            context.current_stage = "analyzing_schema"
            schema_result = await self.schema_analyst.analyze_schema_for_query(context, request)

            if not schema_result["success"]:
                return {
                    "success": False,
                    "error": f"Schema analysis failed: {schema_result.get('error')}",
                    "session_id": session_id,
                }

            # Step 2: Build and execute query
            context.current_stage = "querying"
            query_result = await self.query_builder.build_and_execute_query(
                context, request, schema_result["output"]
            )

            if not query_result["success"]:
                return {
                    "success": False,
                    "error": f"Query execution failed: {query_result.get('error')}",
                    "session_id": session_id,
                }

            # Step 3: Analyze results
            context.current_stage = "analyzing"
            analysis_result = await self.data_analyst.analyze_results(
                context, query_result["output"], request
            )

            # Step 4: Create report (if needed)
            context.current_stage = "reporting"
            if context.output_format == "report":
                report_result = await self.report_writer.create_report(context, analysis_result)
                final_output = report_result["output"]
            else:
                final_output = analysis_result["output"]

            context.current_stage = "completed"

            return {
                "success": True,
                "output": final_output,
                "session_id": session_id,
                "context_summary": context.to_summary(),
                "insights": [insight.dict() for insight in context.insights],
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "stage_failed": context.current_stage,
            }


# Agent registry
AGENTS = {
    "orchestrator": OrchestratorAgent,
    "schema_analyst": SchemaAnalystAgent,
    "query_builder": QueryBuilderAgent,
    "data_analyst": DataAnalystAgent,
    "report_writer": ReportWriterAgent,
}


def get_agent_by_name(name: str) -> Optional[RelationalDataAgent]:
    """
    Get an agent instance by name.

    Args:
        name: Agent name

    Returns:
        Agent instance or None if not found
    """
    agent_class = AGENTS.get(name.lower())
    if agent_class:
        return agent_class()
    return None


def list_agents() -> List[str]:
    """Get list of available agent names."""
    return list(AGENTS.keys())