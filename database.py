import sqlite3
import threading
import logging

logger = logging.getLogger(__name__)

DB_PATH = "/var/data/users.db"

_local = threading.local()


def get_conn():
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id         INTEGER PRIMARY KEY,
            username        TEXT,
            first_name      TEXT,
            payment_status  TEXT DEFAULT 'none',
            order_id        TEXT,
            proof_message_id INTEGER,
            admin_message_id INTEGER,
            selected_payment TEXT,
            support_pending  INTEGER DEFAULT 0,
            last_video_key   TEXT,
            created_at       TEXT,
            request_at       TEXT,
            approved_at      TEXT
        );

        CREATE TABLE IF NOT EXISTS watched (
            user_id    INTEGER,
            video_key  TEXT,
            watched_at TEXT,
            UNIQUE(user_id, video_key)
        );

        CREATE TABLE IF NOT EXISTS sales (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER,
            order_id       TEXT,
            payment_method TEXT,
            amount         REAL DEFAULT 0,
            status         TEXT,
            approved_at    TEXT
        );

        CREATE TABLE IF NOT EXISTS bot_state (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    logger.info("Database initialized ✓")


def db_execute(sql: str, params=()):
    conn = get_conn()
    conn.execute(sql, params)
    conn.commit()


def db_fetchone(sql: str, params=()):
    conn = get_conn()
    row = conn.execute(sql, params).fetchone()
    return row


def db_fetchall(sql: str, params=()):
    conn = get_conn()
    return conn.execute(sql, params).fetchall()
