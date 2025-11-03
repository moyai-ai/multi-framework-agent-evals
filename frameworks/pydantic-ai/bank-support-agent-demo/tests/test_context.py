"""Tests for context models."""

import pytest
from decimal import Decimal
from datetime import datetime

from src.context import (
    BankSupportContext,
    Customer,
    Account,
    AccountType,
    Transaction,
    TransactionType,
    SupportRequest,
    create_initial_context,
    create_test_context,
    context_diff,
    validate_customer_authentication,
    get_account_summary,
)


class TestContextModels:
    """Test context model functionality."""

    def test_create_initial_context(self):
        """Test creating initial context."""
        context = create_initial_context()
        assert isinstance(context, BankSupportContext)
        assert context.session_id != ""
        assert context.authenticated is False
        assert context.current_stage == "greeting"
        assert context.customer is None
        assert context.accounts == []

    def test_create_test_context(self):
        """Test creating test context with data."""
        context = create_test_context(authenticated=True)
        assert context.authenticated is True
        assert context.customer is not None
        assert context.customer.name == "Test User"
        assert len(context.accounts) == 1

    def test_customer_model(self, test_customer):
        """Test Customer model."""
        assert test_customer.id == 1
        assert test_customer.name == "John Doe"
        assert test_customer.email == "john.doe@example.com"
        assert test_customer.is_verified is True

    def test_account_model(self, test_accounts):
        """Test Account model."""
        checking = test_accounts[0]
        assert checking.account_type == AccountType.CHECKING
        assert checking.balance == Decimal("1500.00")
        assert checking.is_active is True

        savings = test_accounts[1]
        assert savings.account_type == AccountType.SAVINGS
        assert savings.balance == Decimal("5000.00")

    def test_transaction_model(self, test_transactions):
        """Test Transaction model."""
        deposit = test_transactions[0]
        assert deposit.transaction_type == TransactionType.DEPOSIT
        assert deposit.amount == Decimal("500.00")
        assert deposit.reference_number != ""

        withdrawal = test_transactions[1]
        assert withdrawal.transaction_type == TransactionType.WITHDRAWAL
        assert withdrawal.amount == Decimal("-50.00")

    def test_context_diff(self):
        """Test context diff tracking."""
        old_context = create_initial_context()
        new_context = create_initial_context()
        new_context.authenticated = True
        new_context.customer_id = 1

        diff = context_diff(old_context, new_context)
        assert "authenticated" in diff
        assert diff["authenticated"]["old"] is False
        assert diff["authenticated"]["new"] is True
        assert "customer_id" in diff

    def test_validate_customer_authentication(self, test_context, test_customer):
        """Test authentication validation."""
        # Not authenticated
        context = create_initial_context()
        assert validate_customer_authentication(context) is False

        # Authenticated but no customer
        context.authenticated = True
        assert validate_customer_authentication(context) is False

        # Fully authenticated
        context.customer = test_customer
        context.customer_id = test_customer.id
        assert validate_customer_authentication(context) is True

    def test_get_account_summary(self, test_context, test_accounts):
        """Test account summary generation."""
        # No accounts
        context = create_initial_context()
        summary = get_account_summary(context)
        assert summary == "No accounts found."

        # With accounts
        context.accounts = test_accounts
        summary = get_account_summary(context)
        assert "Checking Account" in summary
        assert "...7890" in summary
        assert "$1,500.00" in summary
        assert "Savings Account" in summary
        assert "...4321" in summary
        assert "$5,000.00" in summary

    def test_support_request_model(self):
        """Test SupportRequest model."""
        request = SupportRequest(
            id=1,
            customer_id=1,
            request_type="technical",
            description="Cannot login to mobile app",
            status="open",
            created_at=datetime.now()
        )
        assert request.status == "open"
        assert request.resolved_at is None
        assert "mobile app" in request.description

    def test_context_with_error(self):
        """Test context with error handling."""
        context = create_initial_context()
        context.error_message = "Authentication failed"
        context.needs_escalation = True

        assert context.error_message == "Authentication failed"
        assert context.needs_escalation is True

    def test_context_actions_tracking(self):
        """Test action tracking in context."""
        context = create_initial_context()
        context.actions_taken.append("Authenticated customer")
        context.actions_taken.append("Retrieved account balance")
        context.actions_taken.append("Created support ticket")

        assert len(context.actions_taken) == 3
        assert "Authenticated customer" in context.actions_taken
        assert "support ticket" in context.actions_taken[2]

    def test_context_query_history(self):
        """Test query history tracking."""
        context = create_initial_context()
        queries = [
            "Check my balance",
            "Transfer funds",
            "Recent transactions"
        ]

        for query in queries:
            context.query_history.append(query)

        assert len(context.query_history) == 3
        assert context.query_history[0] == "Check my balance"
        assert context.query_history[-1] == "Recent transactions"