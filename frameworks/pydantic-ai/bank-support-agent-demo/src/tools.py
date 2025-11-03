"""Tools for bank support operations."""

import json
import aiosqlite
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
import os

from pydantic_ai import RunContext

from .context import (
    BankSupportContext,
    Customer,
    Account,
    AccountType,
    Transaction,
    TransactionType,
    SupportRequest,
)


# Database path from environment or default
DATABASE_PATH = os.getenv("DATABASE_PATH", "src/data/bank_support.db")


def get_db_connection():
    """Get database connection."""
    db_path = Path(DATABASE_PATH)
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return aiosqlite.connect(str(db_path))


async def authenticate_customer(
    ctx: RunContext[BankSupportContext],
    email: str,
    last_four_ssn: str,
) -> str:
    """
    Authenticate a customer using email and last 4 digits of SSN.

    Args:
        ctx: The context for the current conversation
        email: Customer's email address
        last_four_ssn: Last 4 digits of customer's SSN

    Returns:
        Authentication status message
    """
    # In production, this would verify against secure storage
    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT * FROM customers WHERE email = ? AND ssn_last_four = ?",
            (email, last_four_ssn)
        )
        row = await cursor.fetchone()

        if row:
            # Create Customer object from row
            customer = Customer(
                id=row[0],
                name=row[1],
                email=row[2],
                phone=row[3],
                created_at=datetime.fromisoformat(row[4]),
                is_verified=row[5] if len(row) > 5 else True
            )

            # Update context
            ctx.deps.authenticated = True
            ctx.deps.customer = customer
            ctx.deps.customer_id = customer.id
            ctx.deps.current_stage = "authenticated"

            # Load customer accounts
            cursor = await db.execute(
                "SELECT * FROM accounts WHERE customer_id = ? AND is_active = 1",
                (customer.id,)
            )
            account_rows = await cursor.fetchall()

            ctx.deps.accounts = []
            for acc_row in account_rows:
                account = Account(
                    id=acc_row[0],
                    customer_id=acc_row[1],
                    account_type=AccountType(acc_row[2]),
                    account_number=acc_row[3],
                    balance=Decimal(str(acc_row[4])),
                    created_at=datetime.fromisoformat(acc_row[5]),
                    is_active=acc_row[6] if len(acc_row) > 6 else True
                )
                ctx.deps.accounts.append(account)

            return f"Successfully authenticated. Welcome back, {customer.name}!"
        else:
            ctx.deps.error_message = "Authentication failed"
            return "Authentication failed. Please verify your credentials."


async def get_account_balance(
    ctx: RunContext[BankSupportContext],
    account_type: Optional[str] = None,
) -> str:
    """
    Get account balance(s) for authenticated customer.

    Args:
        ctx: The context for the current conversation
        account_type: Optional account type filter (checking, savings, etc.)

    Returns:
        Account balance information
    """
    if not ctx.deps.authenticated:
        return "You must be authenticated to view account balances."

    if not ctx.deps.accounts:
        return "No accounts found for your profile."

    results = []

    for account in ctx.deps.accounts:
        if account_type and account.account_type.value != account_type.lower():
            continue

        results.append({
            "type": account.account_type.value,
            "account_number": f"...{account.account_number[-4:]}",
            "balance": float(account.balance),
            "formatted_balance": f"${account.balance:,.2f}"
        })

    if not results:
        return f"No {account_type} accounts found." if account_type else "No accounts found."

    # Store in context results
    ctx.deps.results = {"accounts": results}

    # Format response
    response = []
    total_balance = Decimal(0)
    for acc in results:
        response.append(f"- {acc['type'].title()} Account {acc['account_number']}: {acc['formatted_balance']}")
        total_balance += Decimal(str(acc['balance']))

    if len(results) > 1:
        response.append(f"\nTotal Balance: ${total_balance:,.2f}")

    return "\n".join(response)


async def get_recent_transactions(
    ctx: RunContext[BankSupportContext],
    account_id: Optional[int] = None,
    days: int = 30,
    limit: int = 10,
) -> str:
    """
    Get recent transactions for customer accounts.

    Args:
        ctx: The context for the current conversation
        account_id: Optional specific account ID
        days: Number of days to look back (default 30)
        limit: Maximum number of transactions to return (default 10)

    Returns:
        Recent transactions as formatted string
    """
    if not ctx.deps.authenticated:
        return "You must be authenticated to view transactions."

    async with get_db_connection() as db:
        # Build query
        if account_id:
            query = """
                SELECT t.*, a.account_type
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                WHERE t.account_id = ? AND t.created_at > ?
                ORDER BY t.created_at DESC LIMIT ?
            """
            params = (account_id, (datetime.now() - timedelta(days=days)).isoformat(), limit)
        else:
            # Get all accounts for customer
            account_ids = [acc.id for acc in ctx.deps.accounts]
            if not account_ids:
                return "No accounts found."

            placeholders = ",".join("?" * len(account_ids))
            query = f"""
                SELECT t.*, a.account_type
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                WHERE t.account_id IN ({placeholders}) AND t.created_at > ?
                ORDER BY t.created_at DESC LIMIT ?
            """
            params = (*account_ids, (datetime.now() - timedelta(days=days)).isoformat(), limit)

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        if not rows:
            return f"No transactions found in the last {days} days."

        transactions = []
        for row in rows:
            trans = Transaction(
                id=row[0],
                account_id=row[1],
                transaction_type=TransactionType(row[2]),
                amount=Decimal(str(row[3])),
                description=row[4],
                created_at=datetime.fromisoformat(row[5]),
                reference_number=row[6]
            )
            transactions.append({
                "date": trans.created_at.strftime("%Y-%m-%d"),
                "type": trans.transaction_type.value,
                "amount": float(trans.amount),
                "description": trans.description,
                "reference": trans.reference_number,
                "account_type": row[7]  # From the JOIN
            })

        # Store in context
        ctx.deps.recent_transactions = [
            Transaction(**{k: v for k, v in t.items() if k != "account_type"})
            for t in transactions[:5]  # Store first 5 in context
        ]
        ctx.deps.results = {"transactions": transactions}

        # Format response
        response = [f"Recent transactions (last {days} days):"]
        for trans in transactions:
            sign = "+" if trans["type"] in ["deposit", "transfer"] else "-"
            response.append(
                f"  {trans['date']} | {sign}${abs(trans['amount']):,.2f} | "
                f"{trans['description']} | Ref: {trans['reference']}"
            )

        return "\n".join(response)


async def transfer_funds(
    ctx: RunContext[BankSupportContext],
    from_account_id: int,
    to_account_id: int,
    amount: float,
    description: str = "Internal transfer",
) -> str:
    """
    Transfer funds between accounts.

    Args:
        ctx: The context for the current conversation
        from_account_id: Source account ID
        to_account_id: Destination account ID
        amount: Amount to transfer
        description: Transfer description

    Returns:
        Transfer status message
    """
    if not ctx.deps.authenticated:
        return "You must be authenticated to transfer funds."

    amount_decimal = Decimal(str(amount))

    # Validate accounts belong to customer
    customer_account_ids = [acc.id for acc in ctx.deps.accounts]
    if from_account_id not in customer_account_ids:
        return "Source account not found or not authorized."
    if to_account_id not in customer_account_ids:
        return "Destination account not found or not authorized."

    async with get_db_connection() as db:
        try:
            # Start transaction
            await db.execute("BEGIN")

            # Check balance
            cursor = await db.execute(
                "SELECT balance FROM accounts WHERE id = ?",
                (from_account_id,)
            )
            row = await cursor.fetchone()
            if not row:
                await db.execute("ROLLBACK")
                return "Source account not found."

            from_balance = Decimal(str(row[0]))
            if from_balance < amount_decimal:
                await db.execute("ROLLBACK")
                return f"Insufficient funds. Available balance: ${from_balance:,.2f}"

            # Update balances
            await db.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (str(amount_decimal), from_account_id)
            )
            await db.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (str(amount_decimal), to_account_id)
            )

            # Record transactions
            import uuid
            ref_number = str(uuid.uuid4())[:8].upper()
            now = datetime.now().isoformat()

            # Debit transaction
            await db.execute(
                """INSERT INTO transactions
                (account_id, transaction_type, amount, description, created_at, reference_number)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (from_account_id, "transfer", str(-amount_decimal), description, now, ref_number)
            )

            # Credit transaction
            await db.execute(
                """INSERT INTO transactions
                (account_id, transaction_type, amount, description, created_at, reference_number)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (to_account_id, "transfer", str(amount_decimal), description, now, ref_number)
            )

            await db.commit()

            # Update context
            ctx.deps.actions_taken.append(f"Transferred ${amount_decimal} from account {from_account_id} to {to_account_id}")
            ctx.deps.results = {
                "transfer": {
                    "amount": float(amount_decimal),
                    "reference": ref_number,
                    "status": "completed"
                }
            }

            return f"Transfer completed successfully. ${amount_decimal:,.2f} transferred. Reference: {ref_number}"

        except Exception as e:
            await db.execute("ROLLBACK")
            ctx.deps.error_message = str(e)
            return f"Transfer failed: {str(e)}"


async def create_support_ticket(
    ctx: RunContext[BankSupportContext],
    request_type: str,
    description: str,
    priority: str = "normal",
) -> str:
    """
    Create a support ticket for the customer.

    Args:
        ctx: The context for the current conversation
        request_type: Type of support request
        description: Detailed description of the issue
        priority: Priority level (low, normal, high, urgent)

    Returns:
        Ticket creation status
    """
    if not ctx.deps.authenticated:
        customer_id = 0  # Anonymous ticket
    else:
        customer_id = ctx.deps.customer_id

    async with get_db_connection() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO support_requests
            (customer_id, request_type, description, status, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (customer_id, request_type, description, "open", priority, now)
        )
        ticket_id = cursor.lastrowid
        await db.commit()

        # Create SupportRequest object
        support_request = SupportRequest(
            id=ticket_id,
            customer_id=customer_id,
            request_type=request_type,
            description=description,
            status="open",
            created_at=datetime.fromisoformat(now)
        )

        # Update context
        ctx.deps.support_request = support_request
        ctx.deps.actions_taken.append(f"Created support ticket #{ticket_id}")

        return f"Support ticket #{ticket_id} created successfully. Our team will review your request shortly."


async def check_fraud_alert(
    ctx: RunContext[BankSupportContext],
    transaction_id: Optional[int] = None,
) -> str:
    """
    Check for fraud alerts on account or specific transaction.

    Args:
        ctx: The context for the current conversation
        transaction_id: Optional specific transaction to check

    Returns:
        Fraud alert status
    """
    if not ctx.deps.authenticated:
        return "You must be authenticated to check fraud alerts."

    async with get_db_connection() as db:
        if transaction_id:
            cursor = await db.execute(
                "SELECT * FROM fraud_alerts WHERE transaction_id = ?",
                (transaction_id,)
            )
        else:
            account_ids = [acc.id for acc in ctx.deps.accounts]
            placeholders = ",".join("?" * len(account_ids))
            cursor = await db.execute(
                f"SELECT * FROM fraud_alerts WHERE account_id IN ({placeholders}) AND status = 'active'",
                account_ids
            )

        rows = await cursor.fetchall()

        if not rows:
            return "No active fraud alerts found on your accounts."

        alerts = []
        for row in rows:
            alerts.append({
                "id": row[0],
                "account_id": row[1],
                "transaction_id": row[2],
                "alert_type": row[3],
                "description": row[4],
                "created_at": row[5],
                "status": row[6]
            })

        ctx.deps.results = {"fraud_alerts": alerts}

        response = ["Active fraud alerts:"]
        for alert in alerts:
            response.append(
                f"  - Alert #{alert['id']}: {alert['description']} "
                f"(Created: {alert['created_at'][:10]})"
            )

        ctx.deps.needs_escalation = True  # Fraud alerts should be escalated
        response.append("\nIMPORTANT: Please contact our fraud department immediately at 1-800-FRAUD-STOP.")

        return "\n".join(response)


async def update_contact_info(
    ctx: RunContext[BankSupportContext],
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> str:
    """
    Update customer contact information.

    Args:
        ctx: The context for the current conversation
        email: New email address
        phone: New phone number

    Returns:
        Update status message
    """
    if not ctx.deps.authenticated:
        return "You must be authenticated to update contact information."

    if not email and not phone:
        return "Please provide at least one field to update (email or phone)."

    async with get_db_connection() as db:
        updates = []
        params = []

        if email:
            updates.append("email = ?")
            params.append(email)
        if phone:
            updates.append("phone = ?")
            params.append(phone)

        params.append(ctx.deps.customer_id)

        query = f"UPDATE customers SET {', '.join(updates)} WHERE id = ?"
        await db.execute(query, params)
        await db.commit()

        # Update context
        if email:
            ctx.deps.customer.email = email
        if phone:
            ctx.deps.customer.phone = phone

        ctx.deps.actions_taken.append(f"Updated contact info: {', '.join(updates)}")

        return "Contact information updated successfully."


async def check_authentication_status(
    ctx: RunContext[BankSupportContext],
) -> str:
    """
    Check if the customer is currently authenticated.

    Args:
        ctx: The context for the current conversation

    Returns:
        Authentication status message
    """
    if ctx.deps.authenticated:
        customer_name = ctx.deps.customer.name if ctx.deps.customer else "Customer"
        return f"Customer {customer_name} is currently authenticated and can access account services."
    else:
        return "Customer is not authenticated. Please authenticate first to access account services."


# Export tools as a list for the agent
BANK_SUPPORT_TOOLS = [
    check_authentication_status,
    authenticate_customer,
    get_account_balance,
    get_recent_transactions,
    transfer_funds,
    create_support_ticket,
    check_fraud_alert,
    update_contact_info,
]


def get_all_tools() -> List:
    """Get all available tools."""
    return BANK_SUPPORT_TOOLS


def get_tool_descriptions() -> List[Dict[str, str]]:
    """Get descriptions of all available tools."""
    return [
        {
            "name": tool.__name__,
            "description": tool.__doc__.split("\n")[1].strip()
            if tool.__doc__ else "No description"
        }
        for tool in BANK_SUPPORT_TOOLS
    ]