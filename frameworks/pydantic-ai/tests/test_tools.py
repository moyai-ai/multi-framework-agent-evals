"""Tests for bank support tools."""

import pytest
from unittest.mock import AsyncMock, Mock
from decimal import Decimal
from datetime import datetime

from pydantic_ai import RunContext
from src.tools import (
    authenticate_customer,
    get_account_balance,
    get_recent_transactions,
    transfer_funds,
    create_support_ticket,
    check_fraud_alert,
    update_contact_info,
    BANK_SUPPORT_TOOLS,
    get_all_tools,
    get_tool_descriptions,
)
from src.context import BankSupportContext, create_test_context


class TestToolRegistry:
    """Test tool registry and helper functions."""

    def test_bank_support_tools_list(self):
        """Test BANK_SUPPORT_TOOLS contains all tools."""
        assert len(BANK_SUPPORT_TOOLS) == 7
        tool_names = [t._function.__name__ for t in BANK_SUPPORT_TOOLS]

        expected = [
            "authenticate_customer",
            "get_account_balance",
            "get_recent_transactions",
            "transfer_funds",
            "create_support_ticket",
            "check_fraud_alert",
            "update_contact_info"
        ]

        for name in expected:
            assert name in tool_names

    def test_get_all_tools(self):
        """Test getting all tools."""
        tools = get_all_tools()
        assert len(tools) == len(BANK_SUPPORT_TOOLS)
        assert tools == BANK_SUPPORT_TOOLS

    def test_get_tool_descriptions(self):
        """Test getting tool descriptions."""
        descriptions = get_tool_descriptions()
        assert len(descriptions) == len(BANK_SUPPORT_TOOLS)

        for desc in descriptions:
            assert "name" in desc
            assert "description" in desc
            assert desc["description"] != "No description"


@pytest.mark.asyncio
class TestAuthenticationTool:
    """Test authentication tool."""

    async def test_authenticate_success(self, test_database):
        """Test successful authentication."""
        context = create_test_context(authenticated=False)
        ctx = RunContext(data=context)

        result = await authenticate_customer(
            ctx,
            email="test@example.com",
            last_four_ssn="1234"
        )

        assert "Successfully authenticated" in result
        assert context.authenticated is True
        assert context.customer is not None
        assert context.customer_id == 1

    async def test_authenticate_failure(self, test_database):
        """Test failed authentication."""
        context = create_test_context(authenticated=False)
        ctx = RunContext(data=context)

        result = await authenticate_customer(
            ctx,
            email="wrong@example.com",
            last_four_ssn="0000"
        )

        assert "Authentication failed" in result
        assert context.authenticated is False
        assert context.customer is None


@pytest.mark.asyncio
class TestAccountBalanceTool:
    """Test account balance tool."""

    async def test_get_balance_authenticated(self, test_context, test_accounts):
        """Test getting balance when authenticated."""
        test_context.accounts = test_accounts
        ctx = RunContext(data=test_context)

        result = await get_account_balance(ctx)

        assert "$" in result
        assert "Checking" in result
        assert "Savings" in result
        assert "Total Balance" in result

    async def test_get_balance_not_authenticated(self, initial_context):
        """Test getting balance when not authenticated."""
        ctx = RunContext(data=initial_context)

        result = await get_account_balance(ctx)

        assert "must be authenticated" in result

    async def test_get_balance_specific_account(self, test_context, test_accounts):
        """Test getting balance for specific account type."""
        test_context.accounts = test_accounts
        ctx = RunContext(data=test_context)

        result = await get_account_balance(ctx, account_type="checking")

        assert "Checking" in result
        assert "Savings" not in result
        assert "$1,500.00" in result


@pytest.mark.asyncio
class TestTransactionsTool:
    """Test transactions tool."""

    async def test_get_transactions_authenticated(self, test_database, test_context):
        """Test getting transactions when authenticated."""
        ctx = RunContext(data=test_context)

        result = await get_recent_transactions(ctx)

        # May return no transactions message since test DB might be empty
        assert "transaction" in result.lower() or "no transaction" in result.lower()

    async def test_get_transactions_not_authenticated(self, initial_context):
        """Test getting transactions when not authenticated."""
        ctx = RunContext(data=initial_context)

        result = await get_recent_transactions(ctx)

        assert "must be authenticated" in result


@pytest.mark.asyncio
class TestTransferTool:
    """Test fund transfer tool."""

    async def test_transfer_not_authenticated(self, initial_context):
        """Test transfer when not authenticated."""
        ctx = RunContext(data=initial_context)

        result = await transfer_funds(
            ctx,
            from_account_id=1,
            to_account_id=2,
            amount=100.0,
            description="Test transfer"
        )

        assert "must be authenticated" in result

    async def test_transfer_invalid_account(self, test_context, test_accounts):
        """Test transfer with invalid account."""
        test_context.accounts = test_accounts
        ctx = RunContext(data=test_context)

        result = await transfer_funds(
            ctx,
            from_account_id=999,  # Invalid account
            to_account_id=2,
            amount=100.0
        )

        assert "not found" in result or "not authorized" in result


@pytest.mark.asyncio
class TestSupportTicketTool:
    """Test support ticket creation."""

    async def test_create_ticket_authenticated(self, test_database, test_context):
        """Test creating ticket when authenticated."""
        ctx = RunContext(data=test_context)

        result = await create_support_ticket(
            ctx,
            request_type="technical",
            description="Cannot login to mobile app",
            priority="high"
        )

        assert "ticket #" in result.lower()
        assert "created successfully" in result
        assert test_context.support_request is not None

    async def test_create_ticket_anonymous(self, test_database, initial_context):
        """Test creating anonymous ticket."""
        ctx = RunContext(data=initial_context)

        result = await create_support_ticket(
            ctx,
            request_type="general",
            description="Question about account types"
        )

        assert "ticket #" in result.lower()
        assert initial_context.support_request is not None
        assert initial_context.support_request.customer_id == 0


@pytest.mark.asyncio
class TestFraudAlertTool:
    """Test fraud alert checking."""

    async def test_check_fraud_not_authenticated(self, initial_context):
        """Test checking fraud when not authenticated."""
        ctx = RunContext(data=initial_context)

        result = await check_fraud_alert(ctx)

        assert "must be authenticated" in result

    async def test_check_fraud_no_alerts(self, test_database, test_context, test_accounts):
        """Test checking fraud with no alerts."""
        test_context.accounts = test_accounts
        ctx = RunContext(data=test_context)

        result = await check_fraud_alert(ctx)

        assert "No active fraud alerts" in result


@pytest.mark.asyncio
class TestUpdateContactTool:
    """Test contact info update tool."""

    async def test_update_contact_not_authenticated(self, initial_context):
        """Test updating contact when not authenticated."""
        ctx = RunContext(data=initial_context)

        result = await update_contact_info(
            ctx,
            email="new@example.com"
        )

        assert "must be authenticated" in result

    async def test_update_contact_no_fields(self, test_context):
        """Test updating with no fields provided."""
        ctx = RunContext(data=test_context)

        result = await update_contact_info(ctx)

        assert "provide at least one field" in result