import time
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import ADMIN_ID, PAYMENT_TEXTS, FAQ_TEXT, COURSE_OVERVIEW_TEXT, VIDEO_CATALOG, TOTAL_VIDEOS, COURSE_PRICE
from database import db_execute, db_fetchone, db_fetchall
from helpers import (
    ensure_user, get_user_approved, get_payment_label, generate_order_id,
    now_str, find_video, progress_bar, is_admin, get_state, set_state
)
from keyboards import main_menu_keyboard, payment_keyboard

logger = logging.getLogger(__name__)


# ─── /start ──────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)
    paid = get_user_approved(user.id)
    welcome_text = (
        "السلام عليكم ورحمة الله وبركاته 🙋🏻‍♂️\n\n"
        "💎 أهلاً بكم في بوت Economy Trader 💎\n\n"
        "هنا سوف نكون معكم لتعليم التداول من البداية حتى الاحتراف 💱🥇\n\n"
        f"سعر الكورس هو {COURSE_PRICE}$ أو ما يعادلها بالليرة السورية 💲\n\n"
        "اختر من القائمة الرئيسية 👇"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(paid))


# ─── القائمة الرئيسية ─────────────────────────────────────────────────────────
async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    ensure_user(user.id, user.username, user.first_name)
    paid = get_user_approved(user.id)

    if query.data == "menu_home":
        await query.message.reply_text("🏠 القائمة الرئيسية:", reply_markup=main_menu_keyboard(paid))

    elif query.data == "menu_course":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 شراء الكورس",              callback_data="menu_buy")],
            [InlineKeyboardButton("🏠 رجوع للقائمة الرئيسية",   callback_data="menu_home")],
        ])
        await query.message.reply_text(COURSE_OVERVIEW_TEXT, reply_markup=kb)

    elif query.data == "menu_buy":
        if paid:
            await query.message.reply_text("✅ أنت مشترك بالفعل في الكورس! يمكنك الوصول للمكتبة مباشرة.",
                                           reply_markup=main_menu_keyboard(True))
            return
        await query.message.reply_text("💳 اختر طريقة الدفع المناسبة:", reply_markup=payment_keyboard())

    elif query.data == "menu_faq":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 رجوع للقائمة الرئيسية", callback_data="menu_home")]])
        await query.message.reply_text(FAQ_TEXT, reply_markup=kb)

    elif query.data == "menu_support":
        db_execute("UPDATE users SET support_pending=1 WHERE user_id=?", (user.id,))
        await query.message.reply_text("📩 اكتب رسالتك الآن وسيتم إرسالها إلى الدعم مباشرة.")


# ─── الدفع ────────────────────────────────────────────────────────────────────
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data
    text = PAYMENT_TEXTS.get(method, "راسل الأدمن لمعرفة طريقة الدفع.")

    row = db_fetchone("SELECT payment_status, order_id FROM users WHERE user_id=?", (query.from_user.id,))
    current_status   = row[0] if row else "none"
    existing_order_id = row[1] if row else None

    if current_status in ("pending", "reviewing"):
        await query.message.reply_text(
            f"⏳ لديك طلب قيد المراجعة بالفعل.\n🧾 رقم الطلب: {existing_order_id or '-'}"
        )
        return

    order_id = generate_order_id()
    db_execute("UPDATE users SET selected_payment=?, order_id=? WHERE user_id=?",
               (method, order_id, query.from_user.id))

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ أرسلت الدفع", callback_data="paid")],
        [InlineKeyboardButton("⬅️ رجوع",        callback_data="menu_buy")],
    ])
    await query.edit_message_text(
        f"{text}\n\n🧾 رقم طلبك: {order_id}\n\nبعد الدفع اضغط «أرسلت الدفع» وأرسل صورة إشعار الدفع.",
        reply_markup=kb
    )


async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📸 أرسل صورة إشعار الدفع الآن.\n\n⚠️ يجب أن تكون صورة واضحة وحديثة.")


# ─── استقبال إثبات الدفع ──────────────────────────────────────────────────────
async def receive_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)

    if not update.message.photo:
        return

    row = db_fetchone(
        "SELECT payment_status, order_id, selected_payment FROM users WHERE user_id=?",
        (user.id,)
    )
    current_status    = row[0] if row else "none"
    current_order_id  = row[1] if row else None
    selected_payment  = row[2] if row else None

    if current_status in ("pending", "reviewing"):
        await update.message.reply_text(
            f"⏳ لديك طلب قيد المراجعة بالفعل.\n🧾 رقم الطلب: {current_order_id or '-'}"
        )
        return

    # التحقق من أن الصورة حديثة (خلال 2 دقيقة)
    if time.time() - update.message.date.timestamp() > 120:
        await update.message.reply_text("❌ يرجى إرسال صورة إشعار جديدة من الكاميرا.")
        return

    photo    = update.message.photo[-1].file_id
    order_id = current_order_id or generate_order_id()
    payment_method = get_payment_label(selected_payment)

    db_execute(
        "UPDATE users SET proof_message_id=?, payment_status='pending', request_at=?, order_id=? WHERE user_id=?",
        (update.message.message_id, now_str(), order_id, user.id)
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👁 بدء المراجعة",  callback_data=f"review_{user.id}")],
        [InlineKeyboardButton("✅ قبول الدفع",    callback_data=f"approve_{user.id}")],
        [InlineKeyboardButton("❌ رفض الدفع",     callback_data=f"reject_{user.id}")],
    ])
    caption = (
        f"📥 طلب دفع جديد\n\n"
        f"🧾 رقم الطلب: {order_id}\n"
        f"👤 المستخدم: {user.first_name}\n"
        f"🆔 ID: {user.id}\n"
        f"👤 Username: @{user.username or 'بدون'}\n"
        f"💳 طريقة الدفع: {payment_method}\n"
        f"📌 الحالة: pending"
    )
    sent = await context.bot.send_photo(ADMIN_ID, photo=photo, caption=caption, reply_markup=kb)
    db_execute("UPDATE users SET admin_message_id=? WHERE user_id=?", (sent.message_id, user.id))
    await update.message.reply_text(f"✅ تم إرسال الإشعار للمراجعة.\n🧾 رقم طلبك: {order_id}")


# ─── مراجعة / قبول / رفض الدفع ───────────────────────────────────────────────
async def review_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("غير مسموح", show_alert=True)
        return

    user_id = int(query.data.split("_")[1])
    row = db_fetchone("SELECT order_id, selected_payment FROM users WHERE user_id=?", (user_id,))
    order_id         = row[0] if row else "غير معروف"
    selected_payment = row[1] if row else None

    db_execute("UPDATE users SET payment_status='reviewing' WHERE user_id=?", (user_id,))

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ قبول الدفع", callback_data=f"approve_{user_id}")],
        [InlineKeyboardButton("❌ رفض الدفع",  callback_data=f"reject_{user_id}")],
    ])
    await query.edit_message_caption(
        caption=(
            f"📥 طلب دفع قيد المراجعة\n\n"
            f"🧾 رقم الطلب: {order_id}\n"
            f"🆔 ID: {user_id}\n"
            f"💳 طريقة الدفع: {get_payment_label(selected_payment)}\n"
            f"📌 الحالة: reviewing"
        ),
        reply_markup=kb
    )


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("غير مسموح", show_alert=True)
        return

    user_id = int(query.data.split("_")[1])

    # جلب بيانات المستخدم
    try:
        user = await context.bot.get_chat(user_id)
        name          = user.first_name
        username_text = f"@{user.username}" if user.username else "لا يوجد"
    except Exception:
        name          = str(user_id)
        username_text = "غير معروف"

    row = db_fetchone(
        "SELECT proof_message_id, selected_payment, order_id, admin_message_id FROM users WHERE user_id=?",
        (user_id,)
    )
    proof_message_id = row[0] if row else None
    selected_payment = row[1] if row else None
    order_id         = row[2] if row else "غير معروف"
    admin_message_id = row[3] if row else None

    approved_at = now_str()
    db_execute("UPDATE users SET payment_status='approved', approved_at=? WHERE user_id=?", (approved_at, user_id))
    db_execute(
        "INSERT INTO sales (user_id, order_id, payment_method, amount, status, approved_at) VALUES (?,?,?,?,?,?)",
        (user_id, order_id, get_payment_label(selected_payment), COURSE_PRICE, "approved", approved_at)
    )

    # حذف صورة الإثبات من محادثة المستخدم
    if proof_message_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=proof_message_id)
        except Exception:
            pass

    # تعديل رسالة الأدمن
    try:
        if admin_message_id:
            await context.bot.edit_message_caption(
                chat_id=ADMIN_ID,
                message_id=admin_message_id,
                caption=(
                    f"✅ تم قبول الدفع\n\n"
                    f"🧾 رقم الطلب: {order_id}\n"
                    f"👤 الاسم: {name}\n"
                    f"🔗 اليوزر: {username_text}\n"
                    f"🆔 ID: {user_id}\n"
                    f"💳 الطريقة: {get_payment_label(selected_payment)}\n"
                    f"🕒 وقت القبول: {approved_at}"
                )
            )
        else:
            await query.message.delete()
    except Exception:
        pass

    await context.bot.send_message(
        user_id,
        "✅ تم قبول دفعتك! يمكنك الآن الوصول إلى مكتبة الفيديوهات.\n\nاضغط /start للبدء."
    )
    logger.info("Payment approved for user %s, order %s", user_id, order_id)


async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("غير مسموح", show_alert=True)
        return

    user_id = int(query.data.split("_")[1])

    try:
        user = await context.bot.get_chat(user_id)
        name          = user.first_name
        username_text = f"@{user.username}" if user.username else "لا يوجد"
    except Exception:
        name          = str(user_id)
        username_text = "غير معروف"

    row = db_fetchone(
        "SELECT selected_payment, order_id, admin_message_id FROM users WHERE user_id=?",
        (user_id,)
    )
    selected_payment = row[0] if row else None
    order_id         = row[1] if row else "غير معروف"
    admin_message_id = row[2] if row else None

    db_execute("UPDATE users SET payment_status='rejected' WHERE user_id=?", (user_id,))
    db_execute(
        "INSERT INTO sales (user_id, order_id, payment_method, amount, status, approved_at) VALUES (?,?,?,?,?,?)",
        (user_id, order_id, get_payment_label(selected_payment), COURSE_PRICE, "rejected", now_str())
    )

    await context.bot.send_message(
        user_id,
        f"❌ تم رفض إشعار الدفع.\n\n🧾 رقم الطلب: {order_id}\nيرجى إرسال صورة أوضح لإثبات الدفع."
    )

    try:
        if admin_message_id:
            await context.bot.delete_message(chat_id=ADMIN_ID, message_id=admin_message_id)
        else:
            await query.message.delete()
    except Exception:
        pass

    await context.bot.send_message(
        ADMIN_ID,
        f"❌ تم رفض الدفع\n\n"
        f"🧾 رقم الطلب: {order_id}\n"
        f"👤 الاسم: {name}\n"
        f"🔗 اليوزر: {username_text}\n"
        f"🆔 ID: {user_id}\n"
        f"💳 الطريقة: {get_payment_label(selected_payment)}\n"
        f"📎 الإشعار غير صحيح"
    )
    logger.info("Payment rejected for user %s, order %s", user_id, order_id)


# ─── مكتبة الفيديوهات ─────────────────────────────────────────────────────────
async def library(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not get_user_approved(query.from_user.id):
        await query.message.reply_text(
            "❌ يجب أن تشتري الكورس أولاً للوصول إلى المكتبة.",
            reply_markup=main_menu_keyboard(False)
        )
        return

    keyboard = [[InlineKeyboardButton(section["title"], callback_data=sk)]
                for sk, section in VIDEO_CATALOG.items()]
    keyboard += [
        [InlineKeyboardButton("📊 تقدمي في الكورس",    callback_data="progress")],
        [InlineKeyboardButton("▶️ أكمل من آخر درس",    callback_data="continue_last")],
        [InlineKeyboardButton("🆕 ما الجديد",           callback_data="whats_new")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية",    callback_data="menu_home")],
    ]
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
        label = video["title"] + (" 🆕" if video["is_new"] else "")
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

    row = db_fetchone("SELECT COUNT(*) FROM watched WHERE user_id=?", (query.from_user.id,))
    watched_count = row[0] if row else 0
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

    row = db_fetchone("SELECT last_video_key FROM users WHERE user_id=?", (query.from_user.id,))
    last_video_key = row[0] if row else None

    if not last_video_key:
        await query.message.reply_text("ℹ️ لم تشاهد أي فيديو بعد. ابدأ من المكتبة.")
        return

    _, section, video = find_video(last_video_key)
    if not video:
        await query.message.reply_text("⚠️ آخر فيديو غير موجود حالياً.")
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

    watched_rows = db_fetchall("SELECT video_key FROM watched WHERE user_id=?", (query.from_user.id,))
    watched_keys = {r[0] for r in watched_rows}

    lines = []
    for section in VIDEO_CATALOG.values():
        for video in section["videos"]:
            if video["is_new"] and video["key"] not in watched_keys:
                lines.append(f"🆕 {section['title']} - {video['title']}")

    if not lines:
        await query.message.reply_text("✅ لا يوجد دروس جديدة غير مشاهدة حالياً.")
        return

    await query.message.reply_text("🆕 الدروس الجديدة:\n\n" + "\n".join(lines))


async def videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ لا يمكنك مشاهدة الفيديو قبل تأكيد الدفع.")
        return

    _, _, video = find_video(query.data)
    if not video:
        return

    file_id = video["file_id"]
    if not file_id or "PLACEHOLDER" in file_id:
        await query.message.reply_text("⚠️ هذا الفيديو لم يتم رفعه بعد.")
        return

    db_execute(
        "INSERT OR IGNORE INTO watched (user_id, video_key, watched_at) VALUES (?,?,?)",
        (query.from_user.id, query.data, now_str())
    )
    db_execute(
        "UPDATE users SET last_video_key=? WHERE user_id=?",
        (query.data, query.from_user.id)
    )

    await context.bot.send_video(
        chat_id=query.from_user.id,
        video=file_id,
        protect_content=True
    )


# ─── الدعم والإعلانات ─────────────────────────────────────────────────────────
async def support_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)

    # الأدمن يرسل إعلاناً عبر البوت
    if is_admin(user.id) and get_state("broadcast_pending") == "1":
        message = update.message.text
        rows = db_fetchall("SELECT user_id FROM users WHERE payment_status='approved'")
        sent = 0
        for row in rows:
            try:
                await context.bot.send_message(row[0], f"📢 إعلان جديد\n\n{message}")
                sent += 1
            except Exception:
                pass
        set_state("broadcast_pending", "0")
        await update.message.reply_text(f"✅ تم إرسال الإعلان إلى {sent} مستخدم.")
        return

    # رسالة دعم عادية
    row = db_fetchone("SELECT support_pending FROM users WHERE user_id=?", (user.id,))
    if not (row and row[0] == 1):
        return

    await context.bot.send_message(
        ADMIN_ID,
        f"📩 رسالة دعم جديدة\n\n"
        f"👤 المستخدم: {user.first_name}\n"
        f"🆔 ID: {user.id}\n"
        f"👤 Username: @{user.username or 'بدون'}\n\n"
        f"📝 الرسالة:\n{update.message.text}"
    )
    db_execute("UPDATE users SET support_pending=0 WHERE user_id=?", (user.id,))
    await update.message.reply_text("✅ تم إرسال رسالتك إلى الدعم.")
