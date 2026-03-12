import os
import sqlite3
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 728810082

VIDEO_CATALOG = {
    "idea1": {
        "title": "📚 المصطلحات الأساسية",
        "description": "في هذا القسم ستتعلم أهم المصطلحات الأساسية في عالم التداول من البداية.",
        "videos": [
            {"key": "video1", "title": "🎥 أنواع أسواق المال", "file_id": "PLACEHOLDER_VIDEO_1", "is_new": True},
            {"key": "video2", "title": "🎥 مزايا الفوركس", "file_id": "PLACEHOLDER_VIDEO_2", "is_new": True},
            {"key": "video3", "title": "🎥 العملات المتداولة", "file_id": "PLACEHOLDER_VIDEO_3", "is_new": False},
            {"key": "video4", "title": "🎥 أزواج العملات", "file_id": "PLACEHOLDER_VIDEO_4", "is_new": False},
            {"key": "video5", "title": "🎥 أحجام العقود", "file_id": "PLACEHOLDER_VIDEO_5", "is_new": False},
            {"key": "video6", "title": "🎥 النقطة وكيفية حساب الأرباح", "file_id": "PLACEHOLDER_VIDEO_6", "is_new": False},
            {"key": "video7", "title": "🎥 الرافعة المالية", "file_id": "PLACEHOLDER_VIDEO_7", "is_new": False},
        ],
    },

    "idea2": {
        "title": "🏛️ التحليل الأساسي",
        "description": "في هذا القسم ستتعلم التحليل الأساسي وتأثير المؤشرات الاقتصادية والسياسية على السوق.",
        "videos": [
            {"key": "video8", "title": "🎥 معنى التحليل الأساسي", "file_id": "PLACEHOLDER_VIDEO_8", "is_new": True},
            {"key": "video9", "title": "🎥 معدل الفائدة وتأثيره - الجزء الأول", "file_id": "PLACEHOLDER_VIDEO_9", "is_new": True},
            {"key": "video10", "title": "🎥 معدل الفائدة وتأثيره - الجزء الثاني", "file_id": "PLACEHOLDER_VIDEO_10", "is_new": False},
            {"key": "video11", "title": "🎥 الناتج المحلي الإجمالي - الجزء الأول", "file_id": "PLACEHOLDER_VIDEO_11", "is_new": False},
            {"key": "video12", "title": "🎥 الناتج المحلي الإجمالي - الجزء الثاني", "file_id": "PLACEHOLDER_VIDEO_12", "is_new": False},
            {"key": "video13", "title": "🎥 معدل البطالة", "file_id": "PLACEHOLDER_VIDEO_13", "is_new": False},
            {"key": "video14", "title": "🎥 التضخم وأنواعه - الجزء الأول", "file_id": "PLACEHOLDER_VIDEO_14", "is_new": False},
            {"key": "video15", "title": "🎥 التضخم وأنواعه - الجزء الثاني", "file_id": "PLACEHOLDER_VIDEO_15", "is_new": False},
            {"key": "video16", "title": "🎥 الأحداث السياسية والتجارة الدولية وتأثيرها", "file_id": "PLACEHOLDER_VIDEO_16", "is_new": False},
        ],
    },

    "idea3": {
        "title": "📈 التحليل الفني",
        "description": "في هذا القسم ستتعلم التحليل الفني وأهم الأدوات والمؤشرات والنماذج المستخدمة في قراءة السوق.",
        "videos": [
            {"key": "video17", "title": "🎥 القمم والقيعان", "file_id": "PLACEHOLDER_VIDEO_17", "is_new": True},
            {"key": "video18", "title": "🎥 الاتجاه الصاعد والهابط - الجزء الأول", "file_id": "PLACEHOLDER_VIDEO_18", "is_new": True},
            {"key": "video19", "title": "🎥 الاتجاه الصاعد والهابط - الجزء الثاني", "file_id": "PLACEHOLDER_VIDEO_19", "is_new": False},
            {"key": "video20", "title": "🎥 الدعم والمقاومة - الجزء الأول", "file_id": "PLACEHOLDER_VIDEO_20", "is_new": False},
            {"key": "video21", "title": "🎥 الدعم والمقاومة - الجزء الثاني", "file_id": "PLACEHOLDER_VIDEO_21", "is_new": False},
            {"key": "video22", "title": "🎥 مؤشر RSI", "file_id": "PLACEHOLDER_VIDEO_22", "is_new": False},
            {"key": "video23", "title": "🎥 مؤشر Stochastic - الجزء الأول", "file_id": "PLACEHOLDER_VIDEO_23", "is_new": False},
            {"key": "video24", "title": "🎥 مؤشر Stochastic - الجزء الثاني", "file_id": "PLACEHOLDER_VIDEO_24", "is_new": False},
            {"key": "video25", "title": "🎥 مؤشر MACD - الجزء الأول", "file_id": "PLACEHOLDER_VIDEO_25", "is_new": False},
            {"key": "video26", "title": "🎥 مؤشر MACD - الجزء الثاني", "file_id": "PLACEHOLDER_VIDEO_26", "is_new": False},
            {"key": "video27", "title": "🎥 فيبوناتشي", "file_id": "PLACEHOLDER_VIDEO_27", "is_new": False},
            {"key": "video28", "title": "🎥 النظرية الموجية", "file_id": "PLACEHOLDER_VIDEO_28", "is_new": False},
            {"key": "video29", "title": "🎥 الفراغات السعرية", "file_id": "PLACEHOLDER_VIDEO_29", "is_new": False},
            {"key": "video30", "title": "🎥 النماذج السعرية الكلاسيكية - الجزء الأول", "file_id": "PLACEHOLDER_VIDEO_30", "is_new": False},
            {"key": "video31", "title": "🎥 النماذج السعرية الكلاسيكية - الجزء الثاني", "file_id": "PLACEHOLDER_VIDEO_31", "is_new": False},
            {"key": "video32", "title": "🎥 النماذج السعرية الكلاسيكية - الجزء الثالث", "file_id": "PLACEHOLDER_VIDEO_32", "is_new": False},
        ],
    },

    "idea4": {
        "title": "🕯️ الشموع اليابانية",
        "description": "في هذا القسم ستتعلم قراءة الشموع اليابانية وأهم النماذج المستخدمة في التحليل.",
        "videos": [
            {"key": "video33", "title": "🎥 مقدمة عن الشموع اليابانية", "file_id": "PLACEHOLDER_VIDEO_33", "is_new": True},
            {"key": "video34", "title": "🎥 المطرقة والمطرقة المقلوبة والرجل المشنوق", "file_id": "PLACEHOLDER_VIDEO_34", "is_new": True},
            {"key": "video35", "title": "🎥 نجمة الصباح ونجمة المساء", "file_id": "PLACEHOLDER_VIDEO_35", "is_new": False},
            {"key": "video36", "title": "🎥 شمعة الدوجي", "file_id": "PLACEHOLDER_VIDEO_36", "is_new": False},
            {"key": "video37", "title": "🎥 الشموع عالية الظلال", "file_id": "PLACEHOLDER_VIDEO_37", "is_new": False},
            {"key": "video38", "title": "🎥 الابتلاع الشرائي والبيعي", "file_id": "PLACEHOLDER_VIDEO_38", "is_new": False},
            {"key": "video39", "title": "🎥 السحابة القاتمة والخط الثاقب", "file_id": "PLACEHOLDER_VIDEO_39", "is_new": False},
            {"key": "video40", "title": "🎥 الهرامي الشرائي والبيعي", "file_id": "PLACEHOLDER_VIDEO_40", "is_new": False},
        ],
    },
}

TOTAL_VIDEOS = sum(len(section["videos"]) for section in VIDEO_CATALOG.values())

PAYMENT_TEXTS = {
    "pay_usdt": """
💳 الدفع عبر USDT

BEP20:
0xDBbD77bF4aD00576F66EB8be244E278B813cA8Db

TRC20:
TW15xXADYSPytvCsoGxA9Z988h35HpJtrN
""",
    "pay_syriatel": """
💰 الدفع عبر سيريتل كاش

الرقم:
31623094
""",
    "pay_sham": """
💎 الدفع عبر شام كاش

المعرف:
4d0c06e319a22353274375a58987f44b

اسم الحساب:
مجد غسان القيم
""",
    "pay_bank": """
🏦 تحويل بنكي

IBAN:
بنك البركة
1270444
""",
    "pay_cash": """
💵 حوالة نقدية

الاسم:
مجد غسان القيم
الهاتف:
0937872522
""",
}

FAQ_TEXT = """
❓ الأسئلة الشائعة

1) هل الوصول إلى الكورس دائم؟
نعم، الوصول دائم بعد تأكيد الدفع.

2) هل أستطيع مشاهدة الفيديوهات أكثر من مرة؟
نعم.

3) ماذا أفعل إذا تم رفض إشعار الدفع؟
أرسل صورة أوضح لإشعار الدفع ثم أعد المحاولة.

4) هل يمكن إعادة توجيه الفيديوهات؟
لا، الفيديوهات محمية داخل البوت.
"""

COURSE_OVERVIEW_TEXT = """
📘 محتوى الكورس

1️⃣ المصطلحات الأساسية
2️⃣ التحليل الأساسي
3️⃣ التحليل الفني
4️⃣ الشموع اليابانية

💲 سعر الكورس: 25$
"""

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    approved INTEGER DEFAULT 0,
    proof_message_id INTEGER,
    selected_payment TEXT,
    support_pending INTEGER DEFAULT 0,
    last_video_key TEXT,
    created_at TEXT,
    approved_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS watched(
    user_id INTEGER,
    video_key TEXT,
    watched_at TEXT,
    UNIQUE(user_id, video_key)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    payment_method TEXT,
    approved_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bot_state(
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

conn.commit()


def now_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def set_state(key: str, value: str):
    cursor.execute(
        "INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()


def get_state(key: str):
    cursor.execute("SELECT value FROM bot_state WHERE key=?", (key,))
    row = cursor.fetchone()
    return row[0] if row else None


def ensure_user(user_id: int, username: str | None, first_name: str | None) -> None:
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, first_name, now_str()))
    cursor.execute("""
        UPDATE users
        SET username=?, first_name=?
        WHERE user_id=?
    """, (username, first_name, user_id))
    conn.commit()


def get_user_approved(user_id: int) -> bool:
    cursor.execute("SELECT approved FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return bool(row and row[0] == 1)


def get_payment_label(payment_key: str | None) -> str:
    mapping = {
        "pay_usdt": "USDT",
        "pay_syriatel": "سيريتل كاش",
        "pay_sham": "شام كاش",
        "pay_bank": "تحويل بنكي",
        "pay_cash": "حوالة نقدية",
    }
    return mapping.get(payment_key or "", "غير محدد")


def progress_bar(current: int, total: int, size: int = 10) -> str:
    if total <= 0:
        return "░" * size
    filled = int((current / total) * size)
    filled = max(0, min(size, filled))
    return "█" * filled + "░" * (size - filled)


def find_video(video_key: str):
    for section_key, section in VIDEO_CATALOG.items():
        for video in section["videos"]:
            if video["key"] == video_key:
                return section_key, section, video
    return None, None, None


def main_menu_keyboard(is_paid: bool):
    keyboard = [
        [InlineKeyboardButton("📘 محتوى الكورس", callback_data="menu_course")],
        [InlineKeyboardButton("💳 شراء الكورس", callback_data="menu_buy")],
        [InlineKeyboardButton("❓ الأسئلة الشائعة", callback_data="menu_faq")],
        [InlineKeyboardButton("📩 الدعم", callback_data="menu_support")],
    ]

    if is_paid:
        keyboard.extend([
            [InlineKeyboardButton("📚 مكتبة الفيديوهات", callback_data="library")],
            [InlineKeyboardButton("▶️ أكمل من آخر درس", callback_data="continue_last")],
            [InlineKeyboardButton("📊 تقدمي في الكورس", callback_data="progress")],
            [InlineKeyboardButton("🆕 ما الجديد", callback_data="whats_new")],
        ])

    return InlineKeyboardMarkup(keyboard)


def payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("USDT", callback_data="pay_usdt")],
        [InlineKeyboardButton("سيريتل كاش", callback_data="pay_syriatel")],
        [InlineKeyboardButton("شام كاش", callback_data="pay_sham")],
        [InlineKeyboardButton("تحويل بنكي", callback_data="pay_bank")],
        [InlineKeyboardButton("حوالة نقدية", callback_data="pay_cash")],
        [InlineKeyboardButton("⬅️ رجوع للقائمة الرئيسية", callback_data="menu_home")],
    ])


def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("💰 آخر المبيعات", callback_data="admin_sales")],
        [InlineKeyboardButton("👥 عدد المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("📢 إرسال إعلان", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🏠 رجوع", callback_data="admin_back")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)

    paid = get_user_approved(user.id)

    welcome_text = """السلام عليكم و رحمة الله و بركاته🙋🏻‍♂️

💎 اهلاً بكم في بوت Economy Trader 💎

هنا سوف نكون معكم لتعليم التداول من البداية حتى الاحتراف 💱🥇

سعر الكورس هو 25$ أو ما يعادلها بالليرة السورية 💲

اختر من القائمة الرئيسية 👇"""

    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_keyboard(paid)
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text(
        "🛠 لوحة الأدمن",
        reply_markup=admin_panel_keyboard()
    )


async def admin_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("غير مسموح", show_alert=True)
        return

    if query.data == "admin_stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE approved=1")
        paid_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sales")
        sales_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM watched")
        watched_count = cursor.fetchone()[0]

        await query.message.reply_text(
            f"📊 إحصائيات البوت\n\n"
            f"👥 عدد المستخدمين: {total_users}\n"
            f"💰 عدد المشترين: {paid_users}\n"
            f"🧾 عدد عمليات البيع: {sales_count}\n"
            f"🎥 عدد المشاهدات المسجلة: {watched_count}"
        )
        return

    if query.data == "admin_sales":
        cursor.execute("""
            SELECT user_id, payment_method, approved_at
            FROM sales
            ORDER BY id DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()

        if not rows:
            await query.message.reply_text("لا توجد مبيعات مسجلة بعد.")
            return

        lines = ["💰 آخر 10 مبيعات:\n"]
        for row in rows:
            lines.append(f"👤 {row[0]} | 💳 {row[1]} | 🕒 {row[2]}")

        await query.message.reply_text("\n".join(lines))
        return

    if query.data == "admin_users":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE approved=1")
        paid_users = cursor.fetchone()[0]

        await query.message.reply_text(
            f"👥 المستخدمون\n\n"
            f"إجمالي المستخدمين: {total_users}\n"
            f"المستخدمون الدافعون: {paid_users}"
        )
        return

    if query.data == "admin_broadcast":
        set_state("broadcast_pending", "1")
        await query.message.reply_text(
            "📢 أرسل الآن نص الإعلان الذي تريد إرساله لكل المشتركين."
        )
        return

    if query.data == "admin_back":
        await query.message.reply_text("🏠 رجعت من لوحة الأدمن.")
        return


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    ensure_user(user.id, user.username, user.first_name)
    paid = get_user_approved(user.id)

    if query.data == "menu_home":
        await query.message.reply_text(
            "🏠 القائمة الرئيسية:",
            reply_markup=main_menu_keyboard(paid)
        )
        return

    if query.data == "menu_course":
        await query.message.reply_text(
            COURSE_OVERVIEW_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 شراء الكورس", callback_data="menu_buy")],
                [InlineKeyboardButton("🏠 رجوع للقائمة الرئيسية", callback_data="menu_home")]
            ])
        )
        return

    if query.data == "menu_buy":
        await query.message.reply_text(
            "💳 اختر طريقة الدفع المناسبة:",
            reply_markup=payment_keyboard()
        )
        return

    if query.data == "menu_faq":
        await query.message.reply_text(
            FAQ_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 رجوع للقائمة الرئيسية", callback_data="menu_home")]
            ])
        )
        return

    if query.data == "menu_support":
        cursor.execute("UPDATE users SET support_pending=1 WHERE user_id=?", (user.id,))
        conn.commit()
        await query.message.reply_text(
            "📩 اكتب رسالتك الآن وسيتم إرسالها إلى الدعم مباشرة."
        )
        return


async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    method = query.data
    text = PAYMENT_TEXTS.get(method, "راسل الأدمن لمعرفة طريقة الدفع.")

    cursor.execute(
        "UPDATE users SET selected_payment=? WHERE user_id=?",
        (method, query.from_user.id)
    )
    conn.commit()

    keyboard = [
        [InlineKeyboardButton("✅ أرسلت الدفع", callback_data="paid")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="menu_buy")],
    ]

    await query.edit_message_text(
        text + "\n\nبعد الدفع اضغط أرسلت الدفع وأرسل صورة إشعار الدفع.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📸 أرسل صورة إشعار الدفع الآن.")


async def receive_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)

    cursor.execute("SELECT support_pending FROM users WHERE user_id=?", (user.id,))
    row = cursor.fetchone()
    support_pending = bool(row and row[0] == 1)

    if support_pending and update.message.text:
        await context.bot.send_message(
            ADMIN_ID,
            f"📩 رسالة دعم جديدة\n\n"
            f"👤 المستخدم: {user.first_name}\n"
            f"🆔 ID: {user.id}\n"
            f"👤 Username: @{user.username if user.username else 'بدون'}\n\n"
            f"📝 الرسالة:\n{update.message.text}"
        )
        cursor.execute("UPDATE users SET support_pending=0 WHERE user_id=?", (user.id,))
        conn.commit()
        await update.message.reply_text("✅ تم إرسال رسالتك إلى الدعم.")
        return

    if not update.message.photo:
        return

    message_time = update.message.date.timestamp()
    current_time = time.time()

    if current_time - message_time > 120:
        await update.message.reply_text(
            "❌ يرجى إرسال صورة إشعار جديدة من الكاميرا."
        )
        return

    photo = update.message.photo[-1].file_id

    cursor.execute(
        "UPDATE users SET proof_message_id=? WHERE user_id=?",
        (update.message.message_id, user.id)
    )
    conn.commit()

    cursor.execute("SELECT selected_payment FROM users WHERE user_id=?", (user.id,))
    payment_row = cursor.fetchone()
    payment_method = get_payment_label(payment_row[0] if payment_row else None)

    keyboard = [
        [InlineKeyboardButton("✅ تم الدفع", callback_data=f"approve_{user.id}")],
        [InlineKeyboardButton("❌ رفض الدفع", callback_data=f"reject_{user.id}")]
    ]

    await context.bot.send_photo(
        ADMIN_ID,
        photo=photo,
        caption=(
            f"إثبات دفع جديد\n\n"
            f"👤 المستخدم: {user.first_name}\n"
            f"🆔 ID: {user.id}\n"
            f"👤 Username: @{user.username if user.username else 'بدون'}\n"
            f"💳 طريقة الدفع: {payment_method}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("✅ تم إرسال الإشعار للمراجعة.")


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("غير مسموح", show_alert=True)
        return

    user_id = int(query.data.split("_")[1])

    cursor.execute("SELECT proof_message_id, selected_payment FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    proof_message_id = row[0] if row else None
    selected_payment = row[1] if row else None

    if proof_message_id:
        try:
            await context.bot.delete_message(
                chat_id=user_id,
                message_id=proof_message_id
            )
        except Exception:
            pass

    approved_at = now_str()

    cursor.execute(
        "UPDATE users SET approved=1, approved_at=? WHERE user_id=?",
        (approved_at, user_id)
    )
    cursor.execute(
        "INSERT INTO sales (user_id, payment_method, approved_at) VALUES (?, ?, ?)",
        (user_id, get_payment_label(selected_payment), approved_at)
    )
    conn.commit()

    keyboard = [
        [InlineKeyboardButton("📚 دخول مكتبة الفيديوهات", callback_data="library")],
        [InlineKeyboardButton("📊 تقدمي في الكورس", callback_data="progress")],
    ]

    await context.bot.send_message(
        user_id,
        "🎉 مبروك!\n\n"
        "تم تأكيد الدفع بنجاح ✅\n\n"
        "📚 يمكنك الآن الوصول إلى مكتبة الفيديوهات الخاصة بالكورس.\n\n"
        "ابدأ أولاً من قسم المصطلحات الأساسية ثم تابع بالترتيب 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await query.edit_message_text(
        f"✅ تم الدفع\n\n"
        f"👤 المستخدم: {user_id}\n"
        f"💳 الطريقة: {get_payment_label(selected_payment)}\n"
        f"📚 تم فتح الوصول إلى الفيديوهات"
    )


async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("غير مسموح", show_alert=True)
        return

    user_id = int(query.data.split("_")[1])

    await context.bot.send_message(
        user_id,
        "❌ إشعار الدفع غير صحيح.\n\n"
        "يرجى التأكد من إرسال صورة واضحة لإشعار الدفع ثم المحاولة مرة أخرى."
    )

    await query.edit_message_text(
        f"❌ تم رفض الإشعار\n\n"
        f"👤 المستخدم: {user_id}\n"
        f"📎 الإشعار غير صحيح"
    )


async def library(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ لا يمكنك دخول المكتبة قبل تأكيد الدفع.")
        return

    keyboard = []
    for section_key, section in VIDEO_CATALOG.items():
        keyboard.append([InlineKeyboardButton(section["title"], callback_data=section_key)])

    keyboard.append([InlineKeyboardButton("📊 تقدمي في الكورس", callback_data="progress")])
    keyboard.append([InlineKeyboardButton("▶️ أكمل من آخر درس", callback_data="continue_last")])
    keyboard.append([InlineKeyboardButton("🆕 ما الجديد", callback_data="whats_new")])
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="menu_home")])

    await query.message.reply_text(
        "📚 مكتبة الفيديوهات\n\nاختر القسم الذي تريد البدء به:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ لا يمكنك دخول هذا القسم قبل تأكيد الدفع.")
        return

    section = VIDEO_CATALOG.get(query.data)
    if not section:
        return

    keyboard = []
    for video in section["videos"]:
        label = video["title"]
        if video["is_new"]:
            label += " 🆕"
        keyboard.append([InlineKeyboardButton(label, callback_data=video["key"])])

    keyboard.append([InlineKeyboardButton("⬅️ رجوع إلى المكتبة", callback_data="library")])

    await query.message.reply_text(
        f"{section['title']}\n\n{section['description']}\n\nاختر الفيديو:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ لا يمكنك مشاهدة التقدم قبل تأكيد الدفع.")
        return

    cursor.execute(
        "SELECT COUNT(*) FROM watched WHERE user_id=?",
        (query.from_user.id,)
    )
    watched_count = cursor.fetchone()[0]
    percent = int((watched_count / TOTAL_VIDEOS) * 100) if TOTAL_VIDEOS > 0 else 0

    await query.message.reply_text(
        f"📊 تقدمك في الكورس\n\n"
        f"{progress_bar(watched_count, TOTAL_VIDEOS)} {percent}%\n\n"
        f"🎥 الفيديوهات التي شاهدتها: {watched_count}/{TOTAL_VIDEOS}"
    )


async def continue_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ يجب تأكيد الدفع أولاً.")
        return

    cursor.execute("SELECT last_video_key FROM users WHERE user_id=?", (query.from_user.id,))
    row = cursor.fetchone()
    last_video_key = row[0] if row else None

    if not last_video_key:
        await query.message.reply_text("ℹ️ لم تشاهد أي فيديو بعد. ابدأ من المكتبة.")
        return

    section_key, section, video = find_video(last_video_key)
    if not video:
        await query.message.reply_text("⚠️ آخر فيديو غير موجود حالياً.")
        return

    if "PLACEHOLDER" in video["file_id"]:
        await query.message.reply_text("⚠️ هذا الفيديو لم يتم رفعه بعد.")
        return

    await context.bot.send_message(
        query.from_user.id,
        f"▶️ آخر درس وصلت له:\n{section['title']} - {video['title']}"
    )

    await context.bot.send_video(
        chat_id=query.from_user.id,
        video=video["file_id"],
        protect_content=True
    )


async def whats_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ يجب تأكيد الدفع أولاً.")
        return

    lines = []
    watched_keys = set()
    cursor.execute("SELECT video_key FROM watched WHERE user_id=?", (query.from_user.id,))
    for row in cursor.fetchall():
        watched_keys.add(row[0])

    for section in VIDEO_CATALOG.values():
        for video in section["videos"]:
            if video["is_new"] and video["key"] not in watched_keys:
                lines.append(f"🆕 {section['title']} - {video['title']}")

    if not lines:
        await query.message.reply_text("لا يوجد دروس جديدة غير مشاهدة حالياً.")
        return

    await query.message.reply_text("🆕 الدروس الجديدة:\n\n" + "\n".join(lines))


async def videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ لا يمكنك مشاهدة الفيديو قبل تأكيد الدفع.")
        return

    section_key, section, video = find_video(query.data)
    if not video:
        return

    file_id = video["file_id"]

    if not file_id or "PLACEHOLDER" in file_id:
        await query.message.reply_text("⚠️ هذا الفيديو لم يتم رفعه بعد.")
        return

    cursor.execute(
        "INSERT OR IGNORE INTO watched (user_id, video_key, watched_at) VALUES (?, ?, ?)",
        (query.from_user.id, query.data, now_str())
    )
    cursor.execute(
        "UPDATE users SET last_video_key=? WHERE user_id=?",
        (query.data, query.from_user.id)
    )
    conn.commit()

    await context.bot.send_video(
        chat_id=query.from_user.id,
        video=file_id,
        protect_content=True
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE approved=1")
    paid_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sales")
    sales_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM watched")
    watched_count = cursor.fetchone()[0]

    await update.message.reply_text(
        f"📊 إحصائيات البوت\n\n"
        f"👥 عدد المستخدمين: {total_users}\n"
        f"💰 عدد المشترين: {paid_users}\n"
        f"🧾 عدد عمليات البيع: {sales_count}\n"
        f"🎥 عدد المشاهدات المسجلة: {watched_count}"
    )


async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    cursor.execute("""
        SELECT user_id, payment_method, approved_at
        FROM sales
        ORDER BY id DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("لا توجد مبيعات مسجلة بعد.")
        return

    lines = ["💰 آخر 10 مبيعات:\n"]
    for row in rows:
        lines.append(f"👤 {row[0]} | 💳 {row[1]} | 🕒 {row[2]}")

    await update.message.reply_text("\n".join(lines))


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("استخدم الأمر هكذا:\n/broadcast نص الرسالة")
        return

    message = " ".join(context.args)

    cursor.execute("SELECT user_id FROM users WHERE approved=1")
    users = [row[0] for row in cursor.fetchall()]

    sent = 0
    for user_id in users:
        try:
            await context.bot.send_message(user_id, f"📢 إعلان جديد\n\n{message}")
            sent += 1
        except Exception:
            pass

    await update.message.reply_text(f"✅ تم إرسال الإعلان إلى {sent} مستخدم.")


async def support_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)

    if is_admin(user.id) and get_state("broadcast_pending") == "1":
        message = update.message.text

        cursor.execute("SELECT user_id FROM users WHERE approved=1")
        users = [row[0] for row in cursor.fetchall()]

        sent = 0
        for user_id in users:
            try:
                await context.bot.send_message(user_id, f"📢 إعلان جديد\n\n{message}")
                sent += 1
            except Exception:
                pass

        set_state("broadcast_pending", "0")
        await update.message.reply_text(f"✅ تم إرسال الإعلان إلى {sent} مستخدم.")
        return

    cursor.execute("SELECT support_pending FROM users WHERE user_id=?", (user.id,))
    row = cursor.fetchone()
    support_pending = bool(row and row[0] == 1)

    if not support_pending:
        return

    await context.bot.send_message(
        ADMIN_ID,
        f"📩 رسالة دعم جديدة\n\n"
        f"👤 المستخدم: {user.first_name}\n"
        f"🆔 ID: {user.id}\n"
        f"👤 Username: @{user.username if user.username else 'بدون'}\n\n"
        f"📝 الرسالة:\n{update.message.text}"
    )

    cursor.execute("UPDATE users SET support_pending=0 WHERE user_id=?", (user.id,))
    conn.commit()

    await update.message.reply_text("✅ تم إرسال رسالتك إلى الدعم.")


if not TOKEN:
    raise ValueError("TOKEN is missing. Set it in Render Environment Variables.")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("sales", sales))
app.add_handler(CommandHandler("broadcast", broadcast))

app.add_handler(CallbackQueryHandler(admin_router, pattern="^admin_"))
app.add_handler(CallbackQueryHandler(menu_router, pattern="^menu_"))
app.add_handler(CallbackQueryHandler(payment, pattern="^pay_"))
app.add_handler(CallbackQueryHandler(paid, pattern="^paid$"))
app.add_handler(CallbackQueryHandler(approve, pattern="^approve_"))
app.add_handler(CallbackQueryHandler(reject, pattern="^reject_"))
app.add_handler(CallbackQueryHandler(library, pattern="^library$"))
app.add_handler(CallbackQueryHandler(ideas, pattern="^idea"))
app.add_handler(CallbackQueryHandler(progress, pattern="^progress$"))
app.add_handler(CallbackQueryHandler(continue_last, pattern="^continue_last$"))
app.add_handler(CallbackQueryHandler(whats_new, pattern="^whats_new$"))
app.add_handler(CallbackQueryHandler(videos, pattern="^video"))

app.add_handler(MessageHandler(filters.PHOTO, receive_proof))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, support_text_handler))

print("Bot Running...")
app.run_polling()
