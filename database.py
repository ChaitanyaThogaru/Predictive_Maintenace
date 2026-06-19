import sqlite3
import time

DB_NAME = "faults.db"

def init_db():
    """Creates the alerts table if it doesn't already exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            severity TEXT,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_alert_to_db(severity, message):
    """Inserts a new predictive alert into the SQL database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO system_alerts (timestamp, severity, message)
        VALUES (?, ?, ?)
    ''', (timestamp_str, severity, message))
    conn.commit()
    conn.close()

def fetch_historical_alerts(limit=10):
    """Retrieves the most recent alerts from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, severity, message 
        FROM system_alerts 
        ORDER BY id DESC 
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    # Format nicely for pandas dataframe display
    return [{"Time": r[0], "Severity": r[1], "Message": r[2]} for r in rows]