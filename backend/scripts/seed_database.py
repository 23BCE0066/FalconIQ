"""
Database Seeder

Generates realistic synthetic financial data for AML testing.
Injects specific typologies:
- Normal behaviour (majority)
- Structuring / Smurfing
- Rapid Cash-Out
- Cross Border High-Risk
- Dormant Account Reactivation
- Circular Transactions
- Layering
"""
import asyncio
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from typing import List

from sqlmodel import Session

# Add backend to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.constants import KYCStatus, RiskLevel, TransactionType, AlertStatus, DetectionType, SessionStatus
from app.database.engine import engine, init_db
import app.database.models
from app.database.models.customer import Customer
from app.database.models.transaction import Transaction
from app.database.models.alert import Alert
from app.database.models.session import AgentSession
from app.database.models.execution_log import AgentExecutionLog
from app.logging.logger import get_logger

logger = get_logger(__name__)

NUM_CUSTOMERS = 1000
NUM_NORMAL_TXS = 23000

COUNTRIES = ["USA", "GBR", "DEU", "FRA", "CAN", "AUS"]
HIGH_RISK_COUNTRIES = ["AFG", "IRN", "PRK", "SYR", "RUS"]

NOW = datetime.now(timezone.utc)


def generate_customers() -> List[Customer]:
    """Generates 1000 customers with varying risk profiles."""
    customers = []
    
    # 1. Normal customers (850)
    for i in range(1, 851):
        customers.append(Customer(
            customer_id=f"CUST_{i}",
            name=f"Customer {i}",
            email=f"customer{i}@example.com",
            annual_income=random.uniform(30000, 150000),
            country=random.choice(COUNTRIES),
            kyc_status=KYCStatus.VERIFIED,
            risk_category=RiskLevel.LOW,
        ))
        
    # 2. High risk / Suspicious customers (150)
    for i in range(851, 1001):
        country = random.choice(COUNTRIES + HIGH_RISK_COUNTRIES)
        risk = RiskLevel.HIGH if country in HIGH_RISK_COUNTRIES else RiskLevel.MEDIUM
        kyc = random.choice([KYCStatus.PENDING, KYCStatus.VERIFIED])
        
        customers.append(Customer(
            customer_id=f"CUST_{i}",
            name=f"Customer {i}",
            email=f"suspicious{i}@example.com",
            annual_income=random.uniform(50000, 500000),
            country=country,
            kyc_status=kyc,
            risk_category=risk,
        ))
        
    return customers


def generate_normal_transactions(customers: List[Customer]) -> List[Transaction]:
    """Generates random normal background noise transactions."""
    txs = []
    cust_ids = [c.customer_id for c in customers]
    
    for _ in range(NUM_NORMAL_TXS):
        sender = random.choice(cust_ids)
        receiver = random.choice(cust_ids)
        while receiver == sender:
            receiver = random.choice(cust_ids)
            
        amount = round(random.uniform(10.0, 3000.0), 2)
        days_ago = random.randint(0, 180)
        hours_ago = random.randint(0, 23)
        ts = NOW - timedelta(days=days_ago, hours=hours_ago)
        
        txs.append(Transaction(
            sender_id=sender,
            receiver_id=receiver,
            amount=amount,
            currency="USD",
            timestamp=ts,
            type=TransactionType.TRANSFER,
            country=random.choice(COUNTRIES),
            is_cross_border=random.random() < 0.1,
            is_weekend=ts.weekday() >= 5,
            is_night=ts.hour < 6 or ts.hour > 22,
        ))
        
    return txs


def generate_structuring() -> List[Transaction]:
    """Generates near-miss reporting threshold transactions (e.g. 5x $9,800)."""
    txs = []
    # Use specific customers so we know who is doing it
    smurfs = ["CUST_901", "CUST_902", "CUST_903"]
    receiver = "CUST_100"
    
    for smurf in smurfs:
        base_ts = NOW - timedelta(days=random.randint(1, 10))
        for i in range(5):
            amount = round(random.uniform(9600.0, 9950.0), 2)
            ts = base_ts + timedelta(hours=i * 2)
            txs.append(Transaction(
                sender_id=smurf, receiver_id=receiver, amount=amount, currency="USD",
                timestamp=ts, type=TransactionType.TRANSFER,
                country="USA", is_cross_border=False, is_weekend=False, is_night=False
            ))
    return txs


def generate_rapid_cashout() -> List[Transaction]:
    """Large incoming transfer followed by immediate cash withdrawals."""
    txs = []
    mule = "CUST_910"
    
    # Large inbound
    ts = NOW - timedelta(days=2)
    txs.append(Transaction(
        sender_id="CUST_500", receiver_id=mule, amount=45000.0, currency="USD",
        timestamp=ts, type=TransactionType.TRANSFER,
        country="USA", is_cross_border=False, is_weekend=False, is_night=False
    ))
    
    # Rapid cashouts
    for i in range(5):
        cash_ts = ts + timedelta(hours=i+1)
        txs.append(Transaction(
            sender_id=mule, receiver_id=mule, amount=8500.0, currency="USD",
            timestamp=cash_ts, type=TransactionType.CASH_OUT,
            country="USA", is_cross_border=False, is_weekend=False, is_night=False
        ))
    return txs


def generate_cross_border() -> List[Transaction]:
    """High volume to high-risk countries."""
    txs = []
    sender = "CUST_920"
    for i in range(15):
        ts = NOW - timedelta(days=random.randint(1, 30))
        txs.append(Transaction(
            sender_id=sender, receiver_id=f"CUST_{100+i}", amount=random.uniform(5000, 15000), 
            currency="USD", timestamp=ts, type=TransactionType.TRANSFER,
            country=random.choice(HIGH_RISK_COUNTRIES), is_cross_border=True, 
            is_weekend=ts.weekday() >= 5, is_night=False
        ))
    return txs


def generate_dormant_reactivation() -> List[Transaction]:
    """Account inactive for 200 days, suddenly transfers large amount."""
    txs = []
    dormant_acc = "CUST_930"
    
    # Old tx
    old_ts = NOW - timedelta(days=210)
    txs.append(Transaction(
        sender_id=dormant_acc, receiver_id="CUST_10", amount=50.0, currency="USD",
        timestamp=old_ts, type=TransactionType.PAYMENT,
        country="USA", is_cross_border=False, is_weekend=False, is_night=False
    ))
    
    # Sudden large tx
    new_ts = NOW - timedelta(days=1)
    txs.append(Transaction(
        sender_id=dormant_acc, receiver_id="CUST_950", amount=85000.0, currency="USD",
        timestamp=new_ts, type=TransactionType.TRANSFER,
        country="USA", is_cross_border=False, is_weekend=False, is_night=False
    ))
    return txs


def generate_layering() -> List[Transaction]:
    """Long chain of transfers moving same funds A -> B -> C -> D -> E."""
    txs = []
    chain = ["CUST_940", "CUST_941", "CUST_942", "CUST_943", "CUST_944"]
    amount = 120000.0
    ts = NOW - timedelta(days=5)
    
    for i in range(len(chain) - 1):
        amount = amount * random.uniform(0.95, 0.99) # Subtract 'fees'
        ts = ts + timedelta(hours=random.randint(1, 4))
        txs.append(Transaction(
            sender_id=chain[i], receiver_id=chain[i+1], amount=amount, currency="USD",
            timestamp=ts, type=TransactionType.TRANSFER,
            country="USA", is_cross_border=False, is_weekend=False, is_night=False
        ))
    return txs


def generate_circular() -> List[Transaction]:
    """Funds flow in a circle: A -> B -> C -> A."""
    txs = []
    chain = ["CUST_950", "CUST_951", "CUST_952"]
    amount = 55000.0
    ts = NOW - timedelta(days=3)
    
    # A -> B -> C
    for i in range(len(chain) - 1):
        amount = amount * 0.98
        ts = ts + timedelta(hours=2)
        txs.append(Transaction(
            sender_id=chain[i], receiver_id=chain[i+1], amount=amount, currency="USD",
            timestamp=ts, type=TransactionType.TRANSFER,
            country="USA", is_cross_border=False, is_weekend=False, is_night=False
        ))
        
    # C -> A
    amount = amount * 0.98
    ts = ts + timedelta(hours=2)
    txs.append(Transaction(
        sender_id=chain[-1], receiver_id=chain[0], amount=amount, currency="USD",
        timestamp=ts, type=TransactionType.TRANSFER,
        country="USA", is_cross_border=False, is_weekend=False, is_night=False
    ))
    return txs


def seed() -> None:
    """Main seeder function."""
    logger.info("Starting database seed...")
    from sqlmodel import SQLModel
    SQLModel.metadata.drop_all(engine)
    init_db()
    
    customers = generate_customers()
    logger.info(f"Generated {len(customers)} customers.")
    
    txs = []
    txs.extend(generate_normal_transactions(customers))
    txs.extend(generate_structuring())
    txs.extend(generate_rapid_cashout())
    txs.extend(generate_cross_border())
    txs.extend(generate_dormant_reactivation())
    txs.extend(generate_layering())
    txs.extend(generate_circular())
    
    # Sort transactions chronologically
    txs.sort(key=lambda x: x.timestamp)
    logger.info(f"Generated {len(txs)} transactions (including typologies).")
    
    alerts = generate_alerts(customers, txs)
    
    from sqlmodel import text
    
    with Session(engine) as session:
        # Clear existing
        session.execute(text("DELETE FROM alerts"))
        session.execute(text("DELETE FROM transactions"))
        session.execute(text("DELETE FROM customers"))
        
        # Batch insert customers
        session.add_all(customers)
        session.commit()
        
        # Batch insert transactions
        chunk_size = 5000
        for i in range(0, len(txs), chunk_size):
            session.add_all(txs[i:i+chunk_size])
            session.commit()
            logger.info(f"Inserted tx batch {i // chunk_size + 1}")
            
        # Insert alerts
        session.add_all(alerts)
        session.commit()
        logger.info(f"Inserted {len(alerts)} alerts.")

        # Clear and insert agent sessions & execution logs
        try:
            session.execute(text("DELETE FROM agent_execution_logs"))
            session.execute(text("DELETE FROM agent_sessions"))
        except Exception:
            pass
        agent_sessions, agent_logs = generate_investigations_and_logs()
        session.add_all(agent_sessions)
        session.commit()
        session.add_all(agent_logs)
        session.commit()
        logger.info(f"Inserted {len(agent_sessions)} agent investigations and {len(agent_logs)} execution logs.")

    logger.info("Database seeding complete!")


def generate_investigations_and_logs():
    logger.info("Generating AI agent investigations and execution logs...")
    sessions = []
    logs = []
    queries = [
        ("Analyze transaction network for CUST_910 for rapid cash-out patterns", "NETWORK_ANALYZE", SessionStatus.COMPLETED, 3450.5, ["CustomerProfileTool", "TransactionQueryTool", "NetworkAnalyzerTool"]),
        ("Check suspicious near-threshold structuring transfers from CUST_901 and CUST_902", "TRANSACTION_AUDIT", SessionStatus.COMPLETED, 2180.2, ["TransactionQueryTool", "RuleEvaluationTool"]),
        ("Assess overall compliance risk and origin risk for CUST_920 cross-border volume", "RISK_ASSESS", SessionStatus.COMPLETED, 1890.0, ["CustomerProfileTool", "SanctionScreeningTool", "RiskScoringTool"]),
        ("Trace long fund movement layering chain A -> B -> C -> D starting at CUST_940", "LAYERING_TRACE", SessionStatus.COMPLETED, 4120.8, ["NetworkAnalyzerTool", "TransactionQueryTool"]),
        ("Investigate dormant account reactivation transfer of $85,000 from CUST_930", "ANOMALY_DETECT", SessionStatus.COMPLETED, 1540.3, ["CustomerProfileTool", "TransactionQueryTool"]),
        ("Verify sanction status and entity screening for CUST_988", "SANCTION_CHECK", SessionStatus.COMPLETED, 980.1, ["SanctionScreeningTool"]),
        ("Inspect circular funnel network involving CUST_950, CUST_951, and CUST_952", "NETWORK_ANALYZE", SessionStatus.COMPLETED, 3760.4, ["NetworkAnalyzerTool"]),
        ("Perform automated enhanced due diligence on high-risk profile CUST_870", "DUE_DILIGENCE", SessionStatus.RUNNING, None, ["CustomerProfileTool", "RiskScoringTool"]),
        ("Query anomalous off-hours wire transfers originating in DEU territory", "ANOMALY_DETECT", SessionStatus.COMPLETED, 2650.0, ["TransactionQueryTool"]),
        ("Evaluate potential smurfing behavior across cluster CUST_903", "TRANSACTION_AUDIT", SessionStatus.FAILED, 1200.0, ["TransactionQueryTool"]),
    ]
    
    import json
    for i, (q, intent, status, time_ms, tools) in enumerate(queries):
        sess_id = f"sess_seed_{100+i}"
        created = NOW - timedelta(days=random.randint(0, 10), hours=random.randint(1, 23), minutes=random.randint(0, 59))
        completed = created + timedelta(milliseconds=time_ms) if time_ms else None
        
        sessions.append(AgentSession(
            session_id=sess_id,
            query=q,
            intent=intent,
            execution_plan=json.dumps(tools),
            status=status,
            total_execution_time_ms=time_ms,
            created_at=created,
            completed_at=completed,
            error_log="Tool timeout on secondary sanction screening API" if status == SessionStatus.FAILED else None
        ))
        
        for step_idx, tool_name in enumerate(tools):
            step_time = round(time_ms / len(tools), 1) if time_ms else 450.0
            logs.append(AgentExecutionLog(
                log_id=f"log_seed_{sess_id}_{step_idx}",
                session_id=sess_id,
                tool_name=tool_name,
                step_order=step_idx,
                success=True if status != SessionStatus.FAILED or step_idx < len(tools) - 1 else False,
                execution_time_ms=step_time,
                duration_ms=step_time,
                confidence=0.95,
                explanation=f"Executed {tool_name} successfully for {intent}.",
                summary=f"{tool_name} check completed with confidence 95%.",
                created_at=created + timedelta(milliseconds=step_idx * step_time)
            ))
            
    return sessions, logs


def generate_alerts(customers: List[Customer], txs: List[Transaction]) -> List[Alert]:
    logger.info("Generating compliance alerts...")
    alerts = []
    high_risk_custs = [c for c in customers if c.risk_category in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
    medium_risk_custs = [c for c in customers if c.risk_category == RiskLevel.MEDIUM][:50]
    target_custs = high_risk_custs + medium_risk_custs
    
    rules = [
        "Structuring / Smurfing ($9.5k-$9.9k)",
        "Rapid Cash-Out / Velocity Sweep",
        "Cross-Border High-Risk Origin",
        "Dormant Account Reactivation Spurt",
        "Circular Funnel Network",
        "High-Frequency Transfers Velocity"
    ]
    models = [
        "GNN Network Anomaly v2.4",
        "AutoEncoder Isolation Forest",
        "XGBoost Typology Classifier",
        "Graph Attention Anomaly Detector"
    ]
    patterns = ["STRUCTURING", "RAPID_CASHOUT", "CROSS_BORDER", "DORMANT_ACCOUNT", "LAYERING", "CIRCULAR"]
    statuses = [AlertStatus.PENDING, AlertStatus.UNDER_REVIEW, AlertStatus.APPROVED, AlertStatus.DISMISSED]
    weights = [0.55, 0.25, 0.10, 0.10]
    
    # Map txs by sender_id for fast lookup
    cust_tx_map = {}
    for tx in txs:
        if tx.sender_id not in cust_tx_map:
            cust_tx_map[tx.sender_id] = []
        cust_tx_map[tx.sender_id].append(tx)
        
    for cust in target_custs:
        num_alerts = random.randint(1, 3) if cust.risk_category in (RiskLevel.HIGH, RiskLevel.CRITICAL) else 1
        for _ in range(num_alerts):
            cust_txs = cust_tx_map.get(cust.customer_id, [])
            tx_id = random.choice(cust_txs).transaction_id if cust_txs else None
            det_type = random.choice([DetectionType.RULE, DetectionType.ML, DetectionType.HYBRID])
            score = round(random.uniform(70.0, 99.0), 1) if cust.risk_category in (RiskLevel.HIGH, RiskLevel.CRITICAL) else round(random.uniform(40.0, 69.9), 1)
            
            alerts.append(Alert(
                customer_id=cust.customer_id,
                transaction_id=tx_id,
                detection_type=det_type,
                rule_triggered=random.choice(rules) if det_type in (DetectionType.RULE, DetectionType.HYBRID) else None,
                ml_model=random.choice(models) if det_type in (DetectionType.ML, DetectionType.HYBRID) else None,
                risk_score=score,
                risk_level=cust.risk_category,
                aml_pattern=random.choice(patterns),
                evidence=f'{{"violation_count": {random.randint(2, 15)}, "recent_volume": {round(random.uniform(10000, 150000), 2)}}}',
                status=random.choices(statuses, weights=weights)[0],
                created_at=NOW - timedelta(days=random.randint(0, 25), hours=random.randint(0, 23))
            ))
    logger.info(f"Generated {len(alerts)} compliance alerts.")
    return alerts


if __name__ == "__main__":
    seed()
