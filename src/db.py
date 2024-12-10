import sqlite3
from src.utils.logger import logger

conn = sqlite3.connect('agent.db', check_same_thread=False)
cursor = conn.cursor()

def get_last_processed_timestamp() -> int:
    row = cursor.execute("SELECT value FROM meta WHERE key='last_processed_timestamp'").fetchone()
    return int(row[0]) if row else 0

def set_last_processed_timestamp(timestamp: int):
    cursor.execute("UPDATE meta SET value=? WHERE key='last_processed_timestamp'", (str(timestamp),))
    conn.commit()

def add_job(job_id: str):
    cursor.execute("INSERT OR IGNORE INTO jobs (job_id, state) VALUES (?, 'open')", (job_id,))
    conn.commit()

def set_job_state(job_id: str, state: str):
    cursor.execute("UPDATE jobs SET state=? WHERE job_id=?", (state, job_id))
    conn.commit()

def get_jobs_to_deliver():
    # Deliver results after 2 minutes
    rows = cursor.execute("""
        SELECT job_id FROM jobs 
        WHERE state='taken' AND 
        (strftime('%s','now') - strftime('%s',created_at)) > 120
    """).fetchall()
    return [{"job_id": r[0]} for r in rows]
