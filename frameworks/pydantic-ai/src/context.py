"""Context models for bank support agent."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class AccountType(str, Enum):
    """Types of bank accounts."""
    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"
    CREDIT_CARD = "credit_card"


class TransactionType(str, Enum):
    """Types of bank transactions."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    FEE = "fee"


class Customer(BaseModel):
    """Customer model."""
    id: int
    name: str
    email: str
    phone: str
    created_at: datetime
    is_verified: bool = True


class Account(BaseModel):
    """Bank account model."""
    id: int
    customer_id: int
    account_type: AccountType
    account_number: str
    balance: Decimal
    created_at: datetime
    is_active: bool = True


class Transaction(BaseModel):
    """Transaction model."""
    id: int
    account_id: int
    transaction_type: TransactionType
    amount: Decimal
    description: str
    created_at: datetime
    reference_number: str


class SupportRequest(BaseModel):
    """Support request tracking."""
    id: int
    customer_id: int
    request_type: str
    description: str
    status: str = "open"  # open, in_progress, resolved, escalated
    created_at: datetime
    resolved_at: Optional[datetime] = None


class BankSupportContext(BaseModel):
    """Context for bank support conversations."""

    # Session tracking
    session_id: str = Field(default="", description="Unique session identifier")
    customer_id: Optional[int] = Field(default=None, description="Authenticated customer ID")

    # Current conversation state
    authenticated: bool = Field(default=False, description="Whether customer is authenticated")
    current_stage: str = Field(default="greeting", description="Current conversation stage")

    # Customer data (populated after authentication)
    customer: Optional[Customer] = None
    accounts: List[Account] = Field(default_factory=list)
    recent_transactions: List[Transaction] = Field(default_factory=list)

    # Request tracking
    original_request: str = Field(default="", description="Initial customer request")
    query_history: List[str] = Field(default_factory=list, description="History of customer queries")
    support_request: Optional[SupportRequest] = None

    # Action tracking
    actions_taken: List[str] = Field(default_factory=list, description="Actions performed during session")

    # Results and metadata
    results: Optional[Dict[str, Any]] = Field(default=None, description="Results of operations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Error handling
    error_message: Optional[str] = Field(default=None, description="Any error that occurred")
    needs_escalation: bool = Field(default=False, description="Whether to escalate to human agent")


def create_initial_context(**kwargs) -> BankSupportContext:
    """Factory function to create initial context."""
    import uuid
    context = BankSupportContext(
        session_id=kwargs.get("session_id", str(uuid.uuid4())),
        **{k: v for k, v in kwargs.items() if k != "session_id"}
    )
    return context


def create_test_context(**kwargs) -> BankSupportContext:
    """Factory function for testing with pre-populated data."""
    context = create_initial_context()

    # Set default test values
    test_customer = Customer(
        id=1,
        name="Test User",
        email="test@example.com",
        phone="555-0100",
        created_at=datetime.now(),
        is_verified=True
    )

    test_account = Account(
        id=1,
        customer_id=1,
        account_type=AccountType.CHECKING,
        account_number="1234567890",
        balance=Decimal("1000.00"),
        created_at=datetime.now(),
        is_active=True
    )

    # Apply any overrides
    for key, value in kwargs.items():
        if hasattr(context, key):
            setattr(context, key, value)

    # Set test data if not overridden
    if not context.customer and kwargs.get("authenticated", False):
        context.customer = test_customer
        context.customer_id = test_customer.id
        context.accounts = [test_account]
        context.authenticated = True

    return context


def context_diff(old: BankSupportContext, new: BankSupportContext) -> Dict[str, Any]:
    """Track changes between context states."""
    old_dict = old.model_dump(exclude_none=True)
    new_dict = new.model_dump(exclude_none=True)

    diff = {}
    all_keys = set(old_dict.keys()) | set(new_dict.keys())

    for key in all_keys:
        old_val = old_dict.get(key)
        new_val = new_dict.get(key)

        if old_val != new_val:
            diff[key] = {
                "old": old_val,
                "new": new_val
            }

    return diff


def validate_customer_authentication(context: BankSupportContext) -> bool:
    """Validate if customer is properly authenticated."""
    return (
        context.authenticated
        and context.customer is not None
        and context.customer_id is not None
    )


def get_account_summary(context: BankSupportContext) -> str:
    """Generate account summary text."""
    if not context.accounts:
        return "No accounts found."

    summary = []
    for account in context.accounts:
        summary.append(
            f"- {account.account_type.value.title()} Account "
            f"(...{account.account_number[-4:]}): "
            f"${account.balance:.2f}"
        )

    return "\n".join(summary)