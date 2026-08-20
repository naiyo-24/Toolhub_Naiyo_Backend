from sqlalchemy import Column, Integer, String, Text, Numeric, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class BankStatement(Base):
    __tablename__ = "bank_statements"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("loan_cases.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)

    bank_name = Column(String, nullable=True)
    account_number_masked = Column(String, nullable=True)

    statement_start = Column(Date, nullable=True)
    statement_end = Column(Date, nullable=True)

    total_credits = Column(Numeric(15,2), nullable=True)
    total_debits = Column(Numeric(15,2), nullable=True)

    average_balance = Column(Numeric(15,2), nullable=True)
    highest_balance = Column(Numeric(15,2), nullable=True)
    lowest_balance = Column(Numeric(15,2), nullable=True)

    total_cash_deposits = Column(Numeric(15,2), nullable=True)
    total_cash_withdrawals = Column(Numeric(15,2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    case = relationship("LoanCase")
    document = relationship("Document")

class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(Integer, ForeignKey("bank_statements.id"), nullable=False, index=True)

    transaction_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    reference_number = Column(String, nullable=True)
    transaction_type = Column(String, nullable=False) # CREDIT, DEBIT

    amount = Column(Numeric(15,2), nullable=False)
    balance = Column(Numeric(15,2), nullable=True)
    category = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    statement = relationship("BankStatement")
