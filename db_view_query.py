import sqlite3
import pandas as pd

conn = sqlite3.connect("faults.db")


df = pd.read_sql_query("SELECT * FROM system_alerts", conn)

print("--- CURRENT DATABASE ENTRIES ---")
print(df)

conn.close()