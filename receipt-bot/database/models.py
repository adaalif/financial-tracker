import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint

class TransactionType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    REFUND = "refund"

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    categories: List["Category"] = Relationship(back_populates="user")
    transactions: List["ReceiptTransaction"] = Relationship(back_populates="user")

class Category(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "name"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="categories")
    items: List["ReceiptItem"] = Relationship(back_populates="category")

class ReceiptTransaction(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True) 
    merchant_name: str
    total_amount_cents: int
    currency: str = Field(default="IDR", max_length=3)
    type: TransactionType = Field(default=TransactionType.EXPENSE)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="transactions")
    items: List["ReceiptItem"] = Relationship(
        back_populates="transaction",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class ReceiptItem(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    receipt_id: uuid.UUID = Field(foreign_key="receipttransaction.id", index=True, ondelete="CASCADE")
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    category_id: uuid.UUID = Field(foreign_key="category.id", index=True)
    item_name: str
    amount_cents: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    transaction: ReceiptTransaction = Relationship(back_populates="items")
    category: Category = Relationship(back_populates="items")
