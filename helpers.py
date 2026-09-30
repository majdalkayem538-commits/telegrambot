import random
import logging
from datetime import datetime, UTC
from config import ADMIN_ID, VIDEO_CATALOG, SECTION_ORDER
from database import db_execute, db_fetchone, db_fetchall

logger = logging.getLogger(__name__)


def now_str() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def generate_order_id() -> str:
    return f"ORD-{random.randint(10000, 99999)}"


def set_state(key: str, value: str):
    db_execute(
        "INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)",
        (key, value)
    )


def get_state(key: str) -> str | None:
    row = db_fetchone("SELECT value FROM bot_state WHERE key=?", (key,))
    return row[0] if row else None


def ensure_user(user_id: int, username: str | None, first_name: str | None):
    db_execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, now_str())
    )
    db_execute(
        "UPDATE users SET username=?, first_name=? WHERE user_id=?",
        (username, first_name, user_id)
    )


def get_user_approved(user_id: int) -> bool:
    row = db_fetchone("SELECT payment_status FROM users WHERE user_id=?", (user_id,))
    return bool(row and row[0] == "approved")


def get_payment_label(payment_key: str | None) -> str:
    mapping = {
        "pay_usdt":     "USDT",
        "pay_syriatel": "سيريتل كاش",
        "pay_sham":     "شام كاش",
        "pay_bank":     "تحويل بنكي",
        "pay_cash":     "حوالة نقدية",
    }
    return mapping.get(payment_key or "", "غير محدد")


def progress_bar(current: int, total: int, size: int = 10) -> str:
    filled = int((current / total) * size) if total > 0 else 0
    filled = max(0, min(size, filled))
    return "█" * filled + "░" * (size - filled)


def find_video(video_key: str):
    for section_key, section in VIDEO_CATALOG.items():
        for video in section["videos"]:
            if video["key"] == video_key:
                return section_key, section, video
    return None, None, None


def is_section_unlocked(user_id: int, section_key: str) -> bool:
    """
    idea1-idea5: مفتوحة تلقائياً لكل مستخدم مدفوع.
    idea6: تحتاج إذن يدوي من الأدمن عبر لوحة التحكم.
    """
    if section_key == "idea6":
        row = db_fetchone(
            "SELECT 1 FROM section_access WHERE user_id=? AND section_key='idea6'",
            (user_id,)
        )
        return bool(row)

    return True  # idea1-idea5 مفتوحة لجميع المستخدمين المدفوعين


def grant_idea6(user_id: int):
    db_execute(
        "INSERT OR IGNORE INTO section_access (user_id, section_key) VALUES (?, 'idea6')",
        (user_id,)
    )


def revoke_idea6(user_id: int):
    db_execute(
        "DELETE FROM section_access WHERE user_id=? AND section_key='idea6'",
        (user_id,)
    )


def has_idea6_access(user_id: int) -> bool:
    row = db_fetchone(
        "SELECT 1 FROM section_access WHERE user_id=? AND section_key='idea6'",
        (user_id,)
    )
    return bool(row)
