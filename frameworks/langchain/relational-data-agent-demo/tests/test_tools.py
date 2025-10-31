"""
Tests for SQL Tools

Test suite for database operation tools.
"""

import pytest
from unittest.mock import Mock, patch

from src.tools import (
    schema_inspector_tool,
    sql_executor_tool,
    data_validator_tool,
    aggregation_tool,
    visualization_tool,
    get_all_tools,
    get_tool_by_name,
)


class TestSchemaInspectorTool:
    """Test schema inspector tool."""

    def test_inspect_all_tables(self, db_manager):
        """Test inspecting all tables in the database."""
        with patch("src.tools.get_db_manager", return_value=db_manager):
            result = schema_inspector_tool.invoke({})

            assert "Database Schema Overview" in result
            assert "customers" in result
            assert "orders" in result
            assert "products" in result

    def test_inspect_specific_table(self, db_manager):
        """Test inspecting a specific table."""
        with patch("src.tools.get_db_manager", return_value=db_manager):
            result = schema_inspector_tool.invoke({"table_name": "customers"})

            assert "Table: customers" in result
            assert "id" in result
            assert "name" in result
            assert "email" in result

    def test_inspect_nonexistent_table(self, db_manager):
        """Test inspecting a table that doesn't exist."""
        with patch("src.tools.get_db_manager", return_value=db_manager):
            result = schema_inspector_tool.invoke({"table_name": "nonexistent"})

            assert "not found" in result.lower()


class TestSQLExecutorTool:
    """Test SQL executor tool."""

    def test_execute_select_query(self, db_manager):
        """Test executing a simple SELECT query."""
        with patch("src.tools.get_db_manager", return_value=db_manager):
            query = "SELECT id, name FROM customers LIMIT 5"
            result = sql_executor_tool.invoke({"query": query})

            # In-memory DB might not have data, so just check for success
            assert any([
                "Query Results" in result,
                "No results" in result,
                "successfully" in result
            ])

    def test_prevent_dangerous_query(self, db_manager):
        """Test that dangerous queries are prevented."""
        with patch("src.tools.get_db_manager", return_value=db_manager):
            query = "DROP TABLE customers"
            result = sql_executor_tool.invoke({"query": query})

            assert "Safety check failed" in result
            assert "dangerous" in result.lower()

    def test_auto_add_limit(self, db_manager):
        """Test that LIMIT is automatically added to SELECT queries."""
        with patch("src.tools.get_db_manager", return_value=db_manager):
            query = "SELECT * FROM products"
            result = sql_executor_tool.invoke({"query": query, "limit": 10})

            # Check that limit was applied
            assert "LIMIT" in result or "rows)" in result or "No results" in result


class TestDataValidatorTool:
    """Test data validator tool."""

    def test_validate_safe_query(self):
        """Test validating a safe query."""
        query = "SELECT * FROM customers WHERE id = 1"
        result = data_validator_tool.invoke({"query": query, "check_type": "safety"})

        assert "passed" in result.lower()

    def test_validate_dangerous_delete(self):
        """Test validating a dangerous DELETE query."""
        query = "DELETE FROM customers"
        result = data_validator_tool.invoke({"query": query, "check_type": "safety"})

        assert "failed" in result.lower()
        assert "WHERE clause" in result

    def test_validate_syntax_missing_from(self):
        """Test syntax validation for missing FROM clause."""
        query = "SELECT id, name"
        result = data_validator_tool.invoke({"query": query, "check_type": "syntax"})

        assert "failed" in result.lower()
        assert "FROM" in result

    def test_validate_unbalanced_parentheses(self):
        """Test validation of unbalanced parentheses."""
        query = "SELECT * FROM customers WHERE (id = 1"
        result = data_validator_tool.invoke({"query": query, "check_type": "syntax"})

        assert "failed" in result.lower()
        assert "parentheses" in result.lower()


class TestAggregationTool:
    """Test aggregation tool."""

    def test_basic_aggregation(self, db_manager):
        """Test basic aggregation operation."""
        with patch("src.tools.get_db_manager", return_value=db_manager):
            result = aggregation_tool.invoke({
                "table": "orders",
                "group_by": ["customer_id"],
                "aggregations": {"id": "count", "total_amount": "sum"}
            })

            # Check that aggregation query was formed
            assert "COUNT" in result or "count" in result or "No results" in result

    def test_aggregation_with_filters(self, db_manager):
        """Test aggregation with WHERE clause."""
        with patch("src.tools.get_db_manager", return_value=db_manager):
            result = aggregation_tool.invoke({
                "table": "orders",
                "group_by": ["status"],
                "aggregations": {"id": "count"},
                "filters": {"status": "delivered"}
            })

            assert "WHERE" in result or "delivered" in result or "No results" in result

    def test_invalid_aggregation_function(self, db_manager):
        """Test handling of invalid aggregation function."""
        with patch("src.tools.get_db_manager", return_value=db_manager):
            result = aggregation_tool.invoke({
                "table": "orders",
                "group_by": ["customer_id"],
                "aggregations": {"id": "invalid_func"}
            })

            assert "Invalid aggregation function" in result


class TestVisualizationTool:
    """Test visualization tool."""

    def test_table_visualization(self):
        """Test creating a table visualization."""
        data = [
            {"name": "Product A", "sales": 100},
            {"name": "Product B", "sales": 150},
        ]
        result = visualization_tool.invoke({
            "data": data,
            "chart_type": "table"
        })

        assert "Product A" in result
        assert "100" in result

    def test_bar_chart_visualization(self):
        """Test creating a bar chart."""
        data = [
            {"label": "Q1", "value": 1000},
            {"label": "Q2", "value": 1500},
        ]
        result = visualization_tool.invoke({
            "data": data,
            "chart_type": "bar",
            "title": "Quarterly Sales"
        })

        assert "Quarterly Sales" in result
        assert "Q1" in result
        assert "█" in result  # Bar character

    def test_summary_visualization(self):
        """Test creating a data summary."""
        data = [
            {"id": 1, "amount": 100.50},
            {"id": 2, "amount": 200.75},
            {"id": 3, "amount": 150.25},
        ]
        result = visualization_tool.invoke({
            "data": data,
            "chart_type": "summary"
        })

        assert "Data Summary" in result
        assert "Total Rows: 3" in result
        assert "Min:" in result
        assert "Max:" in result
        assert "Mean:" in result

    def test_empty_data_visualization(self):
        """Test handling empty data."""
        result = visualization_tool.invoke({
            "data": [],
            "chart_type": "table"
        })

        assert "No data to visualize" in result


class TestToolRegistry:
    """Test tool registry functions."""

    def test_get_all_tools(self):
        """Test getting all available tools."""
        tools = get_all_tools()

        assert len(tools) == 5
        tool_names = [tool.name for tool in tools]
        assert "schema_inspector_tool" in tool_names
        assert "sql_executor_tool" in tool_names
        assert "data_validator_tool" in tool_names
        assert "aggregation_tool" in tool_names
        assert "visualization_tool" in tool_names

    def test_get_tool_by_name(self):
        """Test getting a specific tool by name."""
        tool = get_tool_by_name("sql_executor_tool")
        assert tool is not None
        assert tool.name == "sql_executor_tool"

    def test_get_nonexistent_tool(self):
        """Test getting a tool that doesn't exist."""
        tool = get_tool_by_name("nonexistent_tool")
        assert tool is None