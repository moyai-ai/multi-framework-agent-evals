"""
Tests for Relational Data Agents

Comprehensive test suite for all agent components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from src.agents import (
    SchemaAnalystAgent,
    QueryBuilderAgent,
    DataAnalystAgent,
    ReportWriterAgent,
    OrchestratorAgent,
    get_agent_by_name,
    list_agents,
)
from src.context import ConversationContext, QueryResult, QueryType

# Mock for ChatOpenAI to avoid needing API keys in tests
@pytest.fixture(autouse=True)
def mock_openai():
    """Mock OpenAI to avoid API calls in tests."""
    with patch('src.agents.ChatOpenAI') as mock_chat:
        # Create a mock instance that returns proper responses
        mock_instance = MagicMock()
        mock_instance.invoke = AsyncMock(return_value={
            "output": "Test response",
            "intermediate_steps": []
        })
        mock_chat.return_value = mock_instance

        # Also mock create_agent to return a proper mock
        with patch('src.agents.create_agent') as mock_create:
            mock_agent = MagicMock()
            mock_agent.execute = AsyncMock(return_value={
                "output": "Test agent response",
                "intermediate_steps": []
            })
            mock_create.return_value = mock_agent
            yield mock_chat


class TestAgentRegistry:
    """Test agent registry functions."""

    def test_get_agent_by_name_exact(self):
        """Test getting agent by exact name."""
        agent = get_agent_by_name("orchestrator")
        assert agent is not None
        assert isinstance(agent, OrchestratorAgent)

    def test_get_agent_by_name_case_insensitive(self):
        """Test getting agent by name with different case."""
        agent = get_agent_by_name("SCHEMA_ANALYST")
        assert agent is not None
        assert isinstance(agent, SchemaAnalystAgent)

    def test_get_agent_by_name_not_found(self):
        """Test getting non-existent agent."""
        agent = get_agent_by_name("nonexistent")
        assert agent is None

    def test_list_agents(self):
        """Test listing all agents."""
        agents = list_agents()
        assert len(agents) == 5
        expected_agents = ["orchestrator", "schema_analyst", "query_builder", "data_analyst", "report_writer"]
        for agent_name in expected_agents:
            assert agent_name in agents


class TestSchemaAnalystAgent:
    """Test SchemaAnalystAgent functionality."""

    @pytest.mark.asyncio
    async def test_analyze_schema_for_query(self, sample_context):
        """Test schema analysis for a query."""
        agent = SchemaAnalystAgent()

        # Mock the execute method
        with patch.object(agent, "execute") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "output": """
                For this query, we need:
                - Table: customers (for customer information)
                - Table: orders (for order data)
                - Relationship: orders.customer_id -> customers.id
                """,
                "agent": "Schema Analyst"
            }

            result = await agent.analyze_schema_for_query(
                sample_context,
                "Show me customer orders"
            )

            assert result["success"] is True
            assert "customers" in result["output"]
            assert "orders" in result["output"]

            # Check that tables were added to context
            assert "customers" in sample_context.tables_referenced
            assert "orders" in sample_context.tables_referenced


class TestQueryBuilderAgent:
    """Test QueryBuilderAgent functionality."""

    @pytest.mark.asyncio
    async def test_build_and_execute_query(self, sample_context):
        """Test building and executing a query."""
        agent = QueryBuilderAgent()

        # Mock the execute method
        with patch.object(agent, "execute") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "output": "Query executed successfully: SELECT * FROM customers LIMIT 5",
                "intermediate_steps": [
                    (Mock(tool="sql_executor_tool", tool_input={"query": "SELECT * FROM customers LIMIT 5"}),
                     "Results returned")
                ],
                "agent": "Query Builder"
            }

            result = await agent.build_and_execute_query(
                sample_context,
                "Show me all customers"
            )

            assert result["success"] is True
            assert "Query executed" in result["output"]

            # Check that query was tracked in context
            assert len(sample_context.query_history) == 1
            assert sample_context.query_history[0].query == "SELECT * FROM customers LIMIT 5"

    def test_classify_query_simple(self):
        """Test query classification for simple SELECT."""
        agent = QueryBuilderAgent()
        query_type = agent._classify_query("SELECT * FROM customers")
        assert query_type == QueryType.SIMPLE_SELECT

    def test_classify_query_join(self):
        """Test query classification for JOIN query."""
        agent = QueryBuilderAgent()
        query_type = agent._classify_query("SELECT * FROM orders JOIN customers ON orders.customer_id = customers.id")
        assert query_type == QueryType.JOIN

    def test_classify_query_aggregation(self):
        """Test query classification for aggregation query."""
        agent = QueryBuilderAgent()
        query_type = agent._classify_query("SELECT COUNT(*), SUM(amount) FROM orders GROUP BY customer_id")
        assert query_type == QueryType.AGGREGATION


class TestDataAnalystAgent:
    """Test DataAnalystAgent functionality."""

    @pytest.mark.asyncio
    async def test_analyze_results(self, sample_context, sample_query_results):
        """Test analyzing query results."""
        agent = DataAnalystAgent()

        # Mock the execute method
        with patch.object(agent, "execute") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "output": """
                Analysis Results:
                - Alice Johnson is the top customer with 3 orders totaling $1,989.92
                - Average order value across all customers is $1,573.94
                - There's a strong correlation between order frequency and total spend
                """,
                "agent": "Data Analyst"
            }

            result = await agent.analyze_results(
                sample_context,
                str(sample_query_results),
                "Who are the top customers?"
            )

            assert result["success"] is True
            assert "Alice Johnson" in result["output"]
            assert "top customer" in result["output"]

            # Check that insight was added to context
            assert len(sample_context.insights) == 1
            assert sample_context.insights[0].insight_type == "analysis"


class TestReportWriterAgent:
    """Test ReportWriterAgent functionality."""

    @pytest.mark.asyncio
    async def test_create_report(self, sample_context):
        """Test creating a report from analysis."""
        agent = ReportWriterAgent()

        analysis_results = {
            "output": "Top customers identified with high purchase volumes"
        }

        # Mock the execute method
        with patch.object(agent, "execute") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "output": """
                ## Executive Summary
                Analysis of customer purchase data reveals top performers.

                ## Key Findings
                - Customer #1 leads in total purchase value
                - Strong customer retention observed

                ## Recommendations
                - Focus on retaining top customers
                - Implement loyalty programs
                """,
                "agent": "Report Writer"
            }

            result = await agent.create_report(sample_context, analysis_results)

            assert result["success"] is True
            assert "Executive Summary" in result["output"]
            assert "Key Findings" in result["output"]
            assert "Recommendations" in result["output"]


class TestOrchestratorAgent:
    """Test OrchestratorAgent functionality."""

    @pytest.mark.asyncio
    async def test_process_request_success(self):
        """Test successful request processing."""
        agent = OrchestratorAgent()

        # Mock all sub-agents
        with patch.object(agent.schema_analyst, "analyze_schema_for_query") as mock_schema:
            with patch.object(agent.query_builder, "build_and_execute_query") as mock_query:
                with patch.object(agent.data_analyst, "analyze_results") as mock_analysis:

                    mock_schema.return_value = {
                        "success": True,
                        "output": "Schema analyzed: customers and orders tables needed"
                    }

                    mock_query.return_value = {
                        "success": True,
                        "output": "Query results: 5 customers found"
                    }

                    mock_analysis.return_value = {
                        "success": True,
                        "output": "Analysis complete: Top customers identified"
                    }

                    result = await agent.process_request("Show me top customers")

                    assert result["success"] is True
                    assert "session_id" in result
                    assert "context_summary" in result
                    assert result["output"] == "Analysis complete: Top customers identified"

    @pytest.mark.asyncio
    async def test_process_request_schema_failure(self):
        """Test handling schema analysis failure."""
        agent = OrchestratorAgent()

        with patch.object(agent.schema_analyst, "analyze_schema_for_query") as mock_schema:
            mock_schema.return_value = {
                "success": False,
                "error": "Unable to determine schema"
            }

            result = await agent.process_request("Show me invalid data")

            assert result["success"] is False
            assert "Schema analysis failed" in result["error"]

    @pytest.mark.asyncio
    async def test_process_request_query_failure(self):
        """Test handling query execution failure."""
        agent = OrchestratorAgent()

        with patch.object(agent.schema_analyst, "analyze_schema_for_query") as mock_schema:
            with patch.object(agent.query_builder, "build_and_execute_query") as mock_query:

                mock_schema.return_value = {
                    "success": True,
                    "output": "Schema analyzed"
                }

                mock_query.return_value = {
                    "success": False,
                    "error": "SQL syntax error"
                }

                result = await agent.process_request("Show me data")

                assert result["success"] is False
                assert "Query execution failed" in result["error"]

    @pytest.mark.asyncio
    async def test_process_request_with_report_format(self):
        """Test processing request with report format output."""
        agent = OrchestratorAgent()

        with patch.object(agent.schema_analyst, "analyze_schema_for_query") as mock_schema:
            with patch.object(agent.query_builder, "build_and_execute_query") as mock_query:
                with patch.object(agent.data_analyst, "analyze_results") as mock_analysis:
                    with patch.object(agent.report_writer, "create_report") as mock_report:

                        mock_schema.return_value = {"success": True, "output": "Schema analyzed"}
                        mock_query.return_value = {"success": True, "output": "Query results"}
                        mock_analysis.return_value = {"success": True, "output": "Analysis done"}
                        mock_report.return_value = {"success": True, "output": "Formatted report"}

                        # Create a context with report format
                        from src.context import context_manager
                        context = context_manager.create_context("test_session", "Test request")
                        context.output_format = "report"

                        result = await agent.process_request("Show me data", "test_session")

                        assert result["success"] is True
                        assert result["output"] == "Formatted report"
                        mock_report.assert_called_once()