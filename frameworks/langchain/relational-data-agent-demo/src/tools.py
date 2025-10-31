"""
SQL Tools for Database Operations

Provides LangChain tools for interacting with the relational database.
"""

import os
import re
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import pandas as pd
from tabulate import tabulate
from langchain_core.tools import BaseTool, tool
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.database import DatabaseManager


class SchemaInspectorInput(BaseModel):
    """Input for the schema inspector tool."""

    table_name: Optional[str] = Field(
        None, description="Specific table name to inspect. If None, shows all tables."
    )


class SQLExecutorInput(BaseModel):
    """Input for the SQL executor tool."""

    query: str = Field(description="SQL query to execute")
    limit: Optional[int] = Field(100, description="Maximum number of results to return")


class DataValidatorInput(BaseModel):
    """Input for the data validator tool."""

    query: str = Field(description="SQL query to validate")
    check_type: str = Field(
        "safety",
        description="Type of validation: 'safety' for DROP/DELETE checks, 'syntax' for SQL syntax",
    )


class AggregationInput(BaseModel):
    """Input for the aggregation tool."""

    table: str = Field(description="Table name to aggregate from")
    group_by: List[str] = Field(description="Columns to group by")
    aggregations: Dict[str, str] = Field(
        description="Dictionary of column: aggregation_function (e.g., {'amount': 'sum', 'id': 'count'})"
    )
    filters: Optional[Dict[str, Any]] = Field(None, description="WHERE clause conditions")


class VisualizationInput(BaseModel):
    """Input for the visualization tool."""

    data: List[Dict] = Field(description="Data to visualize")
    chart_type: str = Field(
        "table", description="Type of visualization: 'table', 'bar', 'summary'"
    )
    title: Optional[str] = Field(None, description="Title for the visualization")


# Lazy initialization of database manager
_db_manager = None

def get_db_manager():
    """Get or create the database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@tool
def schema_inspector_tool(table_name: Optional[str] = None) -> str:
    """
    Inspect the database schema to understand table structure and relationships.

    Args:
        table_name: Optional specific table to inspect. If None, shows all tables.

    Returns:
        String description of the schema.
    """
    try:
        schema_info = get_db_manager().get_table_info()

        if table_name:
            if table_name not in schema_info:
                return f"Table '{table_name}' not found in database."

            table_info = schema_info[table_name]
            result = f"Table: {table_name}\n"
            result += "=" * 50 + "\n"

            # Columns
            result += "Columns:\n"
            for col in table_info["columns"]:
                pk = " (PK)" if col.get("primary_key") else ""
                nullable = " NULL" if col["nullable"] else " NOT NULL"
                result += f"  - {col['name']}: {col['type']}{pk}{nullable}\n"

            # Foreign keys
            if table_info["foreign_keys"]:
                result += "\nForeign Keys:\n"
                for fk in table_info["foreign_keys"]:
                    result += f"  - {fk['column']} -> {fk['references']}\n"

            return result
        else:
            # Show all tables
            result = "Database Schema Overview\n"
            result += "=" * 50 + "\n\n"

            for table, info in schema_info.items():
                result += f"Table: {table}\n"
                result += f"  Columns: {', '.join([col['name'] for col in info['columns']])}\n"
                if info["foreign_keys"]:
                    result += f"  Relationships: {', '.join([fk['references'].split('.')[0] for fk in info['foreign_keys']])}\n"
                result += "\n"

            return result
    except Exception as e:
        return f"Error inspecting schema: {str(e)}"


@tool
def sql_executor_tool(query: str, limit: int = 100) -> str:
    """
    Execute a SQL query on the database safely.

    Args:
        query: SQL query to execute
        limit: Maximum number of results to return

    Returns:
        Query results formatted as a string.
    """
    try:
        # Basic safety checks
        query_upper = query.upper().strip()

        # Check for dangerous operations
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]
        if any(keyword in query_upper for keyword in dangerous_keywords):
            if not query_upper.startswith("SELECT"):
                return f"Safety check failed: Query contains potentially dangerous operation. Only SELECT queries are allowed."

        # Add limit if not present and it's a SELECT query
        if "SELECT" in query_upper and "LIMIT" not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        # Execute query
        results = get_db_manager().execute_raw_sql(query)

        if not results:
            return "Query executed successfully. No results returned."

        # Format results as table
        df = pd.DataFrame(results)
        table = tabulate(df, headers="keys", tablefmt="grid", showindex=False)

        result_str = f"Query Results ({len(results)} rows):\n\n{table}"

        if len(results) == limit:
            result_str += f"\n\nNote: Results limited to {limit} rows."

        return result_str

    except SQLAlchemyError as e:
        return f"SQL Error: {str(e)}"
    except Exception as e:
        return f"Error executing query: {str(e)}"


@tool
def data_validator_tool(query: str, check_type: str = "safety") -> str:
    """
    Validate a SQL query before execution.

    Args:
        query: SQL query to validate
        check_type: Type of validation ('safety' or 'syntax')

    Returns:
        Validation result message.
    """
    try:
        query_upper = query.upper().strip()
        issues = []

        if check_type == "safety":
            # Check for dangerous operations
            if "DROP" in query_upper:
                issues.append("Query contains DROP statement - this will delete tables")
            if "DELETE" in query_upper and "WHERE" not in query_upper:
                issues.append("DELETE without WHERE clause - this will delete all rows")
            if "TRUNCATE" in query_upper:
                issues.append("Query contains TRUNCATE - this will delete all data")
            if "UPDATE" in query_upper and "WHERE" not in query_upper:
                issues.append("UPDATE without WHERE clause - this will update all rows")

            # Check for potential injection patterns
            if "--" in query or "/*" in query or "*/" in query:
                issues.append("Query contains SQL comment syntax - potential injection risk")
            if ";" in query and query.count(";") > 1:
                issues.append("Multiple statements detected - only single statements allowed")

        elif check_type == "syntax":
            # Basic syntax checks
            if query_upper.startswith("SELECT"):
                if "FROM" not in query_upper:
                    issues.append("SELECT statement missing FROM clause")

            # Check for balanced parentheses
            if query.count("(") != query.count(")"):
                issues.append("Unbalanced parentheses in query")

            # Check for balanced quotes
            single_quotes = query.count("'")
            if single_quotes % 2 != 0:
                issues.append("Unbalanced single quotes in query")

        if issues:
            return f"Validation failed:\n" + "\n".join(f"- {issue}" for issue in issues)
        else:
            return f"Query validation passed ({check_type} check)"

    except Exception as e:
        return f"Error validating query: {str(e)}"


@tool
def aggregation_tool(
    table: str,
    group_by: List[str],
    aggregations: Dict[str, str],
    filters: Optional[Dict[str, Any]] = None
) -> str:
    """
    Perform aggregation operations on database tables.

    Args:
        table: Table name to aggregate from
        group_by: Columns to group by
        aggregations: Dictionary of column: aggregation_function
        filters: Optional WHERE clause conditions

    Returns:
        Aggregation results formatted as a string.
    """
    try:
        # Build aggregation query
        agg_parts = []
        for column, func in aggregations.items():
            func_upper = func.upper()
            if func_upper not in ["SUM", "AVG", "COUNT", "MIN", "MAX"]:
                return f"Invalid aggregation function: {func}"
            agg_parts.append(f"{func_upper}({column}) as {column}_{func.lower()}")

        select_clause = ", ".join(group_by + agg_parts)
        query = f"SELECT {select_clause} FROM {table}"

        # Add filters if provided
        if filters:
            where_parts = []
            for col, val in filters.items():
                if isinstance(val, str):
                    where_parts.append(f"{col} = '{val}'")
                else:
                    where_parts.append(f"{col} = {val}")
            query += f" WHERE {' AND '.join(where_parts)}"

        # Add GROUP BY
        query += f" GROUP BY {', '.join(group_by)}"

        # Execute and return results
        return sql_executor_tool.invoke({"query": query})

    except Exception as e:
        return f"Error performing aggregation: {str(e)}"


@tool
def visualization_tool(
    data: List[Dict],
    chart_type: str = "table",
    title: Optional[str] = None
) -> str:
    """
    Create text-based visualizations of query results.

    Args:
        data: Data to visualize
        chart_type: Type of visualization ('table', 'bar', 'summary')
        title: Optional title for the visualization

    Returns:
        Text-based visualization.
    """
    try:
        if not data:
            return "No data to visualize"

        result = ""
        if title:
            result += f"{title}\n{'=' * len(title)}\n\n"

        if chart_type == "table":
            df = pd.DataFrame(data)
            result += tabulate(df, headers="keys", tablefmt="grid", showindex=False)

        elif chart_type == "bar":
            # Simple text-based bar chart
            df = pd.DataFrame(data)
            if len(df.columns) < 2:
                return "Bar chart requires at least 2 columns (label and value)"

            label_col = df.columns[0]
            value_col = df.columns[1]

            max_val = df[value_col].max()
            scale = 50 / max_val if max_val > 0 else 1

            for _, row in df.iterrows():
                bar_len = int(row[value_col] * scale)
                bar = "█" * bar_len
                result += f"{row[label_col]:20s} | {bar} {row[value_col]:.2f}\n"

        elif chart_type == "summary":
            df = pd.DataFrame(data)
            result += "Data Summary:\n"
            result += "-" * 50 + "\n"
            result += f"Total Rows: {len(df)}\n"
            result += f"Columns: {', '.join(df.columns)}\n\n"

            # Numeric columns summary
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                result += "Numeric Column Statistics:\n"
                for col in numeric_cols:
                    result += f"\n{col}:\n"
                    result += f"  Min: {df[col].min():.2f}\n"
                    result += f"  Max: {df[col].max():.2f}\n"
                    result += f"  Mean: {df[col].mean():.2f}\n"
                    result += f"  Sum: {df[col].sum():.2f}\n"

        return result

    except Exception as e:
        return f"Error creating visualization: {str(e)}"


def get_all_tools() -> List[BaseTool]:
    """
    Get all available SQL tools.

    Returns:
        List of tool instances.
    """
    return [
        schema_inspector_tool,
        sql_executor_tool,
        data_validator_tool,
        aggregation_tool,
        visualization_tool,
    ]


def get_tool_by_name(name: str) -> Optional[BaseTool]:
    """
    Get a tool by its name.

    Args:
        name: Tool name

    Returns:
        Tool instance or None if not found.
    """
    tools = {tool.name: tool for tool in get_all_tools()}
    return tools.get(name)