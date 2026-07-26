"""
Database models package.

Importing all SQLModel table classes here ensures they are registered with
SQLModel.metadata before `init_db()` is called in main.py.
"""
from app.database.models.alert import Alert, AlertCreate, AlertRead, AlertActionRequest
from app.database.models.customer import Customer, CustomerCreate, CustomerRead
from app.database.models.execution_log import AgentExecutionLog
from app.database.models.session import AgentSession
from app.database.models.transaction import Transaction, TransactionCreate, TransactionRead
from app.database.models.report import ReportRecord
from app.database.models.user_dataset import UserDataset

__all__ = [
    "AgentExecutionLog",
    "AgentSession",
    "Alert",
    "AlertActionRequest",
    "AlertCreate",
    "AlertRead",
    "Customer",
    "CustomerCreate",
    "CustomerRead",
    "ReportRecord",
    "Transaction",
    "TransactionCreate",
    "TransactionRead",
    "UserDataset",
]
