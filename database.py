import sqlite3
import threading
from config import COURSE_PRICE

# ─── اتصال آمن مع الـ threads ───────────────────────────────────────────────
_local = threading.local()
DB_PATH = "/var/data/users.db"


def get_conn():
    """إرجاع اتصال خاص بكل thread."""
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn


def get_cursor():
    return get_conn().cursor()


# ─── تهيئة الجداول (تشتغل مرة واحدة عند البدء) ─────────────────────────────
def init_db():
    c = get_conn()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id          INTEGER PRIMARY KEY,
            username         TEXT,
            first_name       TEXT,
            payment_status   TEXT DEFAULT 'none',
            order_id         TEXT,
            proof_message_id INTEGER,
            admin_message_id INTEGER,
            selected_payment TEXT,
            support_pending  INTEGER DEFAULT 0,
            last_video_key   TEXT,
            created_at       TEXT,
            request_at       TEXT,
            approved_at      TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS watched (
            user_id    INTEGER,
            video_key  TEXT,
            watched_at TEXT,
            UNIQUE(user_id, video_key)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER,
            order_id       TEXT,
            payment_method TEXT,
            amount         REAL DEFAULT 25,
            status         TEXT,
            approved_at    TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bot_state (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    c.commit()

    # إضافة أعمدة ناقصة بأمان
    _ensure_column("users", "order_id",         "TEXT")
    _ensure_column("users", "admin_message_id",  "INTEGER")
    _ensure_column("sales", "order_id",          "TEXT")
    _ensure_column("sales", "amount",            f"REAL DEFAULT {COURSE_PRICE}")


def _ensure_column(table: str, column: str, definition: str):
    c = get_conn()
    cur = c.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    existing = [row[1] for row in cur.fetchall()]
    if column not in existing:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        c.commit()


# وظائف مساعدة للاستخدام من الملفات الأخرى
def db_execute(sql: str, params: tuple = ()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    return cur


def db_fetchone(sql: str, params: tuple = ()):
    cur = get_conn().cursor()
    cur.execute(sql, params)
    return cur.fetchone()


def db_fetchall(sql: str, params: tuple = ()):
    cur = get_conn().cursor()
    cur.execute(sql, params)
    return cur.fetchall()
