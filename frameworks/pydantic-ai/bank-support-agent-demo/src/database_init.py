"""Initialize the bank support database with schema and seed data."""

import asyncio
import aiosqlite
from pathlib import Path
from datetime import datetime, timedelta
import os
import random
import uuid
from decimal import Decimal


DATABASE_PATH = os.getenv("DATABASE_PATH", "src/data/bank_support.db")


async def create_tables(db):
    """Create all necessary database tables."""

    # Customers table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            created_at TEXT NOT NULL,
            is_verified INTEGER DEFAULT 1,
            ssn_last_four TEXT NOT NULL
        )
    """)

    # Accounts table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            account_type TEXT NOT NULL,
            account_number TEXT UNIQUE NOT NULL,
            balance REAL NOT NULL,
            created_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    """)

    # Transactions table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            reference_number TEXT UNIQUE NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
    """)

    # Support requests table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS support_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            request_type TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            priority TEXT DEFAULT 'normal',
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    """)

    # Fraud alerts table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS fraud_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            transaction_id INTEGER,
            alert_type TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (account_id) REFERENCES accounts (id),
            FOREIGN KEY (transaction_id) REFERENCES transactions (id)
        )
    """)

    # Create indexes for better performance
    await db.execute("CREATE INDEX IF NOT EXISTS idx_accounts_customer ON accounts(customer_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(created_at)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_support_customer ON support_requests(customer_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_fraud_account ON fraud_alerts(account_id)")

    await db.commit()
    print("✓ Database tables created successfully")


async def insert_seed_data(db):
    """Insert seed data for testing."""

    now = datetime.now()

    # Insert customers
    customers = [
        ("Test User", "test@example.com", "555-0100", "1234"),
        ("John Doe", "john.doe@example.com", "555-0123", "5678"),
        ("Jane Smith", "jane.smith@example.com", "555-0145", "9012"),
        ("Alice Johnson", "alice.j@example.com", "555-0167", "3456"),
        ("Bob Wilson", "bob.w@example.com", "555-0189", "7890"),
    ]

    customer_ids = []
    for name, email, phone, ssn in customers:
        cursor = await db.execute("""
            INSERT OR IGNORE INTO customers (name, email, phone, created_at, ssn_last_four)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, phone, (now - timedelta(days=random.randint(30, 365))).isoformat(), ssn))
        customer_ids.append(cursor.lastrowid)

    print(f"✓ Inserted {len(customers)} customers")

    # Insert accounts for each customer
    account_types = ["checking", "savings", "business", "credit_card"]
    account_ids = []

    for i, customer_id in enumerate(customer_ids):
        if customer_id:  # Check if customer was actually inserted
            # Each customer gets 2-3 accounts
            num_accounts = random.randint(2, 3)
            for j in range(num_accounts):
                account_type = account_types[j % len(account_types)]
                account_number = f"{random.randint(1000, 9999)}{random.randint(100000, 999999)}"
                balance = round(random.uniform(100, 10000), 2)

                cursor = await db.execute("""
                    INSERT OR IGNORE INTO accounts
                    (customer_id, account_type, account_number, balance, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    customer_id,
                    account_type,
                    account_number,
                    balance,
                    (now - timedelta(days=random.randint(30, 365))).isoformat()
                ))
                account_ids.append(cursor.lastrowid)

    print(f"✓ Inserted {len(account_ids)} accounts")

    # Insert transactions for accounts
    transaction_types = ["deposit", "withdrawal", "transfer", "payment", "fee"]
    descriptions = [
        "Direct deposit - Salary",
        "ATM withdrawal",
        "Online transfer",
        "Bill payment - Utilities",
        "Monthly service fee",
        "Mobile deposit",
        "Wire transfer received",
        "Debit card purchase",
        "Interest payment",
        "Overdraft fee"
    ]

    transaction_count = 0
    for account_id in account_ids:
        if account_id:  # Check if account was actually inserted
            # Each account gets 5-15 transactions
            num_transactions = random.randint(5, 15)
            for _ in range(num_transactions):
                trans_type = random.choice(transaction_types)
                amount = round(random.uniform(-500, 1000), 2)
                if trans_type in ["deposit", "transfer"]:
                    amount = abs(amount)  # Deposits are positive
                elif trans_type in ["withdrawal", "payment", "fee"]:
                    amount = -abs(amount)  # Withdrawals are negative

                await db.execute("""
                    INSERT INTO transactions
                    (account_id, transaction_type, amount, description, created_at, reference_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    account_id,
                    trans_type,
                    amount,
                    random.choice(descriptions),
                    (now - timedelta(days=random.randint(0, 30))).isoformat(),
                    str(uuid.uuid4())[:8].upper()
                ))
                transaction_count += 1

    print(f"✓ Inserted {transaction_count} transactions")

    # Insert some support requests
    request_types = ["technical", "account", "fraud", "general", "complaint"]
    request_descriptions = [
        "Cannot login to mobile app",
        "Need to update address",
        "Suspicious transaction on account",
        "Question about fees",
        "Service complaint"
    ]

    for i in range(10):
        customer_id = random.choice(customer_ids) if customer_ids else None
        await db.execute("""
            INSERT INTO support_requests
            (customer_id, request_type, description, status, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            random.choice(request_types),
            random.choice(request_descriptions),
            random.choice(["open", "in_progress", "resolved"]),
            random.choice(["low", "normal", "high"]),
            (now - timedelta(days=random.randint(0, 7))).isoformat()
        ))

    print("✓ Inserted 10 support requests")

    # Insert a few fraud alerts
    for i in range(3):
        account_id = random.choice(account_ids) if account_ids else None
        if account_id:
            await db.execute("""
                INSERT INTO fraud_alerts
                (account_id, alert_type, description, created_at, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                account_id,
                random.choice(["suspicious_login", "unusual_transaction", "potential_fraud"]),
                "Unusual activity detected on account",
                (now - timedelta(days=random.randint(0, 2))).isoformat(),
                "active"
            ))

    print("✓ Inserted 3 fraud alerts")

    await db.commit()


async def verify_database(db):
    """Verify database contents."""

    # Count records in each table
    tables = ["customers", "accounts", "transactions", "support_requests", "fraud_alerts"]
    print("\n📊 Database Statistics:")
    print("-" * 40)

    for table in tables:
        cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
        count = await cursor.fetchone()
        print(f"{table.ljust(20)}: {count[0]} records")

    # Verify test user specifically
    cursor = await db.execute("""
        SELECT c.*, COUNT(a.id) as account_count
        FROM customers c
        LEFT JOIN accounts a ON c.id = a.customer_id
        WHERE c.email = 'test@example.com'
        GROUP BY c.id
    """)
    test_user = await cursor.fetchone()

    if test_user:
        print("\n✓ Test user verified:")
        print(f"  Email: {test_user[2]}")
        print(f"  SSN Last 4: {test_user[6]}")
        print(f"  Accounts: {test_user[7]}")
    else:
        print("\n⚠️  Test user not found!")


async def initialize_database():
    """Main initialization function."""
    print(f"\n🏦 Initializing Bank Support Database")
    print(f"📁 Database path: {DATABASE_PATH}")
    print("=" * 40)

    # Ensure directory exists
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database for fresh start
    if db_path.exists():
        print(f"⚠️  Removing existing database at {db_path}")
        db_path.unlink()

    # Create and populate database
    async with aiosqlite.connect(str(db_path)) as db:
        await create_tables(db)
        await insert_seed_data(db)
        await verify_database(db)

    print("\n✨ Database initialization complete!")
    print("\nTest credentials:")
    print("  Email: test@example.com")
    print("  SSN Last 4: 1234")


def main():
    """Entry point for database initialization."""
    asyncio.run(initialize_database())


if __name__ == "__main__":
    main()