"""Pytest fixtures for bank support tests."""

import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, Mock
import aiosqlite

from src.context import (
    BankSupportContext,
    create_initial_context,
    create_test_context,
    Customer,
    Account,
    AccountType,
    Transaction,
    TransactionType,
)
from src.agents import get_initial_agent, get_agent_by_name
from datetime import datetime
from decimal import Decimal


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def initial_context():
    """Fixture providing initial context."""
    return create_initial_context()


@pytest.fixture
def test_context():
    """Fixture with pre-set test values."""
    return create_test_context(
        authenticated=True,
        customer_id=1,
        session_id="test-session-123"
    )


@pytest.fixture
def test_customer():
    """Fixture providing a test customer."""
    return Customer(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        phone="555-0123",
        created_at=datetime.now(),
        is_verified=True
    )


@pytest.fixture
def test_accounts():
    """Fixture providing test accounts."""
    return [
        Account(
            id=1,
            customer_id=1,
            account_type=AccountType.CHECKING,
            account_number="1234567890",
            balance=Decimal("1500.00"),
            created_at=datetime.now(),
            is_active=True
        ),
        Account(
            id=2,
            customer_id=1,
            account_type=AccountType.SAVINGS,
            account_number="0987654321",
            balance=Decimal("5000.00"),
            created_at=datetime.now(),
            is_active=True
        )
    ]


@pytest.fixture
def test_transactions():
    """Fixture providing test transactions."""
    import uuid
    return [
        Transaction(
            id=1,
            account_id=1,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("500.00"),
            description="Direct deposit",
            created_at=datetime.now(),
            reference_number=str(uuid.uuid4())[:8].upper()
        ),
        Transaction(
            id=2,
            account_id=1,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=Decimal("-50.00"),
            description="ATM withdrawal",
            created_at=datetime.now(),
            reference_number=str(uuid.uuid4())[:8].upper()
        )
    ]


@pytest.fixture
async def test_database():
    """Fixture providing a test database."""
    db_path = "test_bank_support.db"

    # Create test database
    async with aiosqlite.connect(db_path) as db:
        # Create tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                created_at TEXT,
                is_verified INTEGER DEFAULT 1,
                ssn_last_four TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                account_type TEXT,
                account_number TEXT UNIQUE,
                balance REAL,
                created_at TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                account_id INTEGER,
                transaction_type TEXT,
                amount REAL,
                description TEXT,
                created_at TEXT,
                reference_number TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS support_requests (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                request_type TEXT,
                description TEXT,
                status TEXT,
                priority TEXT DEFAULT 'normal',
                created_at TEXT,
                resolved_at TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS fraud_alerts (
                id INTEGER PRIMARY KEY,
                account_id INTEGER,
                transaction_id INTEGER,
                alert_type TEXT,
                description TEXT,
                created_at TEXT,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        """)

        # Insert test data
        await db.execute("""
            INSERT INTO customers (id, name, email, phone, created_at, ssn_last_four)
            VALUES (1, 'Test User', 'test@example.com', '555-0100', ?, '1234')
        """, (datetime.now().isoformat(),))

        await db.execute("""
            INSERT INTO accounts (id, customer_id, account_type, account_number, balance, created_at)
            VALUES (1, 1, 'checking', '1234567890', 1500.00, ?)
        """, (datetime.now().isoformat(),))

        await db.execute("""
            INSERT INTO accounts (id, customer_id, account_type, account_number, balance, created_at)
            VALUES (2, 1, 'savings', '0987654321', 5000.00, ?)
        """, (datetime.now().isoformat(),))

        await db.commit()

    # Set environment variable for tests
    os.environ["DATABASE_PATH"] = db_path

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def mock_openai_response(monkeypatch):
    """Mock OpenAI API response."""
    async def mock_create(*args, **kwargs):
        return AsyncMock(
            choices=[
                Mock(
                    message=Mock(
                        content="Mocked response from OpenAI",
                        role="assistant"
                    )
                )
            ],
            usage=Mock(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15
            )
        )

    monkeypatch.setattr(
        "pydantic_ai.models.openai.AsyncOpenAI.chat.completions.create",
        mock_create
    )


@pytest.fixture
def scenario_files():
    """Fixture providing scenario file paths."""
    scenarios_dir = Path(__file__).parent.parent / "src" / "scenarios"
    return {
        "authentication": scenarios_dir / "authentication_flow.json",
        "fund_transfer": scenarios_dir / "fund_transfer.json",
        "transaction_history": scenarios_dir / "transaction_history.json",
        "support_ticket": scenarios_dir / "support_ticket.json",
        "update_contact": scenarios_dir / "update_contact_info.json",
    }


@pytest.fixture
def api_key():
    """Check if API key is available."""
    return os.environ.get("OPENAI_API_KEY")


@pytest.fixture
def skip_if_no_api_key(api_key):
    """Skip tests that require API key."""
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")


@pytest.fixture
def bank_support_agent():
    """Fixture providing bank support agent."""
    return get_initial_agent()


@pytest.fixture
def fraud_specialist_agent():
    """Fixture providing fraud specialist agent."""
    return get_agent_by_name("fraud_specialist")


@pytest.fixture
def account_specialist_agent():
    """Fixture providing account specialist agent."""
    return get_agent_by_name("account_specialist")