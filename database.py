import sqlite3
from config import COURSE_PRICE

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,username TEXT,first_name TEXT,payment_status TEXT DEFAULT 'none',order_id TEXT,proof_message_id INTEGER,admin_message_id INTEGER,selected_payment TEXT,support_pending INTEGER DEFAULT 0,last_video_key TEXT,created_at TEXT,request_at TEXT,approved_at TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS watched(user_id INTEGER,video_key TEXT,watched_at TEXT,UNIQUE(user_id, video_key))")
cursor.execute("CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,order_id TEXT,payment_method TEXT,amount REAL DEFAULT 25,status TEXT,approved_at TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS bot_state(key TEXT PRIMARY KEY,value TEXT)")
conn.commit()

def ensure_column(table_name: str, column_name: str, definition: str):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
        conn.commit()

ensure_column("users", "order_id", "TEXT")
ensure_column("users", "admin_message_id", "INTEGER")
ensure_column("sales", "order_id", "TEXT")
ensure_column("sales", "amount", "REAL DEFAULT 25")
