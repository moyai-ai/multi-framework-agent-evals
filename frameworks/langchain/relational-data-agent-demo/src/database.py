"""
Database Models and Setup

Defines the relational database schema and provides database initialization utilities.
"""

import os
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    inspect,
    text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from sqlalchemy.sql import func

Base = declarative_base()


class Customer(Base):
    """Customer model representing individuals or businesses."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(50))
    country = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    # Relationships
    orders = relationship("Order", back_populates="customer")


class Product(Base):
    """Product model representing items for sale."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50))
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
    inventory_logs = relationship("InventoryLog", back_populates="product")


class Order(Base):
    """Order model representing customer purchases."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="pending")  # pending, processing, shipped, delivered
    total_amount = Column(Float)
    shipping_address = Column(Text)
    payment_method = Column(String(50))

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """OrderItem model representing individual items within an order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float)

    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")


class InventoryLog(Base):
    """InventoryLog model for tracking stock changes."""

    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    change_type = Column(String(20))  # restock, sale, adjustment, return
    quantity_change = Column(Integer)
    new_quantity = Column(Integer)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text)

    # Relationships
    product = relationship("Product", back_populates="inventory_logs")


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database manager.

        Args:
            database_url: SQLAlchemy database URL. If None, uses environment variable or default.
        """
        # Use absolute path for SQLite database
        # When run as a module, we're in the project root
        default_db_path = os.path.abspath("src/data/relational_demo.db")

        # Ensure the directory exists
        os.makedirs(os.path.dirname(default_db_path), exist_ok=True)

        self.database_url = database_url or os.getenv(
            "DATABASE_URL", f"sqlite:///{default_db_path}"
        )

        self.engine = create_engine(
            self.database_url, echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"
        )

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all tables in the database."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """
        Get a database session.

        Returns:
            A SQLAlchemy session.
        """
        return self.SessionLocal()

    def get_table_info(self) -> dict:
        """
        Get information about all tables in the database.

        Returns:
            Dictionary containing table names and their columns.
        """
        inspector = inspect(self.engine)
        tables_info = {}

        for table_name in inspector.get_table_names():
            columns = []
            for column in inspector.get_columns(table_name):
                column_info = {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                    "primary_key": column.get("primary_key", False),
                }
                columns.append(column_info)

            # Get foreign keys
            foreign_keys = []
            for fk in inspector.get_foreign_keys(table_name):
                foreign_keys.append(
                    {
                        "column": fk["constrained_columns"][0],
                        "references": f"{fk['referred_table']}.{fk['referred_columns'][0]}",
                    }
                )

            tables_info[table_name] = {"columns": columns, "foreign_keys": foreign_keys}

        return tables_info

    def execute_raw_sql(self, query: str, params: dict = None) -> list:
        """
        Execute a raw SQL query.

        Args:
            query: SQL query string
            params: Parameters for the query

        Returns:
            Query results as a list of dictionaries.
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            connection.commit()  # Commit the transaction for INSERT/UPDATE/DELETE
            if result.returns_rows:
                return [dict(row._mapping) for row in result]
            return []


def init_database():
    """Initialize the database with tables."""
    db_manager = DatabaseManager()
    db_manager.create_tables()
    print("Database initialized successfully.")
    return db_manager


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()