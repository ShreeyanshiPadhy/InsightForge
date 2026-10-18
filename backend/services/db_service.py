import sqlite3
from datetime import datetime

DB_NAME = "insightforge.db"

def init_db(db_path: str = DB_NAME):
    """Initializes the SQLite database schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_name TEXT NOT NULL,
            total_accounts INTEGER NOT NULL,
            total_outstanding REAL NOT NULL,
            high_risk_count INTEGER NOT NULL,
            ai_summary_snippet TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_analysis_run(
    file_name: str,
    total_accounts: int,
    total_outstanding: float,
    high_risk_count: int,
    ai_summary_snippet: str = "",
    db_path: str = DB_NAME
) -> int:
    """Logs an analysis run into SQLite."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO analysis_runs 
        (timestamp, file_name, total_accounts, total_outstanding, high_risk_count, ai_summary_snippet)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, file_name, total_accounts, total_outstanding, high_risk_count, ai_summary_snippet[:250]))
    
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id

def get_run_history(limit: int = 10, db_path: str = DB_NAME) -> list:
    """Retrieves recent analysis runs."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analysis_runs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]