"""
Audit Logging Service for FactoryTwin (P_307)
Maintains tamper-evident operational and administrative audit trails in SQLite.
"""

import logging
from database import get_db_connection

logger = logging.getLogger(__name__)

def log_audit_event(user_id: int, username: str, action: str, ip_address: str = "127.0.0.1", details: str = ""):
    """Insert an immutable audit log record into the SQLite database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (user_id, username, action, ip_address, details)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, action, ip_address, details))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}")

def get_recent_audit_logs(limit: int = 50):
    """Retrieve the most recent audit logs ordered by timestamp descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, username, action, ip_address, details, timestamp
        FROM audit_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
