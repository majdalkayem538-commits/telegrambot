import os
import logging
import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import COURSE_PRICE
from database import db_execute, db_fetchone, db_fetchall
from helpers import is_admin, set_state, get_payment_label, grant_idea6, revoke_idea6, has_idea6_access
from keyboards import admin_panel_keyboard, idea6_access_keyboard

logger = logging.getLogger(__name__)


# ─── دوال مشتركة للإحصائيات ──────────────────────────────────────────────────
def _get_stats_text() -> str:
    total_users  = db_fetchone("SELECT COUNT(*) FROM users")[0]
    paid_users   = db_fetchone("SELECT COUNT(*) FROM users WHERE payment_status='approved'")[0]
    sales_count  = db_fetchone("SELECT COUNT(*) FROM sales WHERE status='approved'")[0]
    pending_count= db_fetchone("SELECT COUNT(*) FROM users WHERE payment_status IN ('pending','reviewing')")[0]
    total_profit = db_fetchone("SELECT COALESCE(SUM(amount),0) FROM sales WHERE status='approved'")[0]
    watched_count= db_fetchone("SELECT COUNT(*) FROM watched")[0]

    return (
        f"📊 إحصائيات البوت\n\n"
        f"👥 عدد المستخدمين: {total_users}\n"
        f"💰 عدد المشترين: {paid_users}\n"
        f"🧾 عدد العمليات المقبولة: {sales_count}\n"
        f"📥 عدد الطلبات المعلقة: {pending_count}\n"
        f"💵 إجمالي الأرباح: {total_profit}$\n"
        f"🎥 عدد المشاهدات المسجلة: {watched_count}"
    )


def _get_profit_text() -> str:
    total_profit = db_fetchone("SELECT COALESCE(SUM(amount),0) FROM sales WHERE status='approved'")[0]
    total_sales  = db_fetchone("SELECT COUNT(*) FROM sales WHERE status='approved'")[0]
    today_profit = db_fetchone(
        "SELECT COALESCE(SUM(amount),0) FROM sales WHERE status='approved' AND date(substr(approved_at,1,10))=date('now')"
    )[0]
    today_sales  = db_fetchone(
        "SELECT COUNT(*) FROM sales WHERE status='approved' AND date(substr(approved_at,1,10))=date('now')"
    )[0]

    return (
        f"💰 تقرير الأرباح\n\n"
        f"📈 إجمالي الأرباح: {total_profit}$\n"
        f"🧾 إجمالي العمليات المقبولة: {total_sales}\n\n"
        f"📅 أرباح اليوم: {today_profit}$\n"
        f"✅ عمليات اليوم المقبولة: {today_sales}"
    )


def export_sales_to_excel() -> str:
    rows = db_fetchall(
        "SELECT user_id, order_id, payment_method, amount, status, approved_at FROM sales ORDER BY id DESC"
    )
    df = pd.DataFrame(rows, columns=["User ID", "Order ID", "Payment Method", "Amount", "Status", "Approved At"])
    os.makedirs("exports", exist_ok=True)
    filename = f"exports/sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(filename, index=False, engine="xlsxwriter")
    return filename


# ─── /admin ───────────────────────────────────────────────────────────────────
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("🛠 لوحة الأدمن", reply_markup=admin_panel_keyboard())


# ─── Callback الأدمن ─────────────────────────────────────────────────────────
async def admin_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("غير مسموح", show_alert=True)
        return

    data = query.data

    if data == "admin_stats":
        await query.message.reply_text(_get_stats_text())

    elif data == "admin_sales":
        rows = db_fetchall(
            "SELECT user_id, order_id, payment_method, amount, status, approved_at FROM sales ORDER BY id DESC LIMIT 10"
        )
        if not rows:
            await query.message.reply_text("لا توجد عمليات مسجلة بعد.")
            return
        lines = ["💰 آخر 10 عمليات:\n"]
        for r in rows:
            lines.append(f"👤 {r[0]} | 🧾 {r[1]} | 💳 {r[2]} | 💵 {r[3]}$ | 📌 {r[4]} | 🕒 {r[5]}")
        await query.message.reply_text("\n".join(lines))

    elif data == "admin_pending":
        rows = db_fetchall(
            "SELECT user_id, order_id, selected_payment, request_at, payment_status FROM users "
            "WHERE payment_status IN ('pending','reviewing') ORDER BY request_at DESC"
        )
        if not rows:
            await query.message.reply_text("لا توجد طلبات معلقة حالياً.")
            return
        lines = ["📥 الطلبات المعلقة:\n"]
        for r in rows:
            lines.append(
                f"🧾 {r[1] or '-'} | 👤 {r[0]} | 💳 {get_payment_label(r[2])} | 📌 {r[4]} | 🕒 {r[3]}"
            )
        await query.message.reply_text("\n".join(lines))

    elif data == "admin_users":
        total_users = db_fetchone("SELECT COUNT(*) FROM users")[0]
        paid_users  = db_fetchone("SELECT COUNT(*) FROM users WHERE payment_status='approved'")[0]
        await query.message.reply_text(
            f"👥 المستخدمون\n\nإجمالي المستخدمين: {total_users}\nالمستخدمون الدافعون: {paid_users}"
        )

    elif data == "admin_export_excel":
        file_path = export_sales_to_excel()
        with open(file_path, "rb") as f:
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=f,
                filename=os.path.basename(file_path),
                caption="📁 تم تصدير العمليات إلى ملف Excel"
            )

    elif data == "admin_profit":
        await query.message.reply_text(_get_profit_text())

    elif data == "admin_broadcast":
        set_state("broadcast_pending", "1")
        await query.message.reply_text("📢 أرسل الآن نص الإعلان الذي تريد إرساله لكل المشتركين.")

    elif data == "admin_sections":
        set_state("sections_pending_uid", "1")
        await query.message.reply_text(
            "🔓 إدارة الأقسام\n\n"
            "أرسل معرّف المستخدم (User ID) الذي تريد إدارة وصوله إلى قسم التحليل الفني الاحترافي:"
        )

    elif data.startswith("idea6_grant_") or data.startswith("idea6_revoke_"):
        parts = data.split("_")
        action  = parts[1]   # grant أو revoke
        user_id = int(parts[2])

        if action == "grant":
            grant_idea6(user_id)
            status_text = "✅ تم فتح قسم التحليل الفني الاحترافي للمستخدم."
        else:
            revoke_idea6(user_id)
            status_text = "🔒 تم إغلاق قسم التحليل الفني الاحترافي للمستخدم."

        has_access = has_idea6_access(user_id)
        await query.message.edit_text(
            f"{status_text}\n\n👤 المستخدم: {user_id}\n"
            f"📌 الحالة الحالية: {'مفتوح ✅' if has_access else 'مغلق 🔒'}",
            reply_markup=idea6_access_keyboard(user_id, has_access)
        )

    elif data == "admin_back":
        await query.message.reply_text("🛠 لوحة الأدمن", reply_markup=admin_panel_keyboard())


# ─── أوامر الأدمن النصية ─────────────────────────────────────────────────────
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(_get_stats_text())


async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    rows = db_fetchall(
        "SELECT user_id, order_id, payment_method, amount, status, approved_at FROM sales ORDER BY id DESC LIMIT 10"
    )
    if not rows:
        await update.message.reply_text("لا توجد عمليات مسجلة بعد.")
        return
    lines = ["💰 آخر 10 عمليات:\n"]
    for r in rows:
        lines.append(f"👤 {r[0]} | 🧾 {r[1]} | 💳 {r[2]} | 💵 {r[3]}$ | 📌 {r[4]} | 🕒 {r[5]}")
    await update.message.reply_text("\n".join(lines))


async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يستقبل الرسائل النصية: إذا كانت من الأدمن يعالجها، وإلا يُحيلها لـ support_text_handler."""
    from handlers_content import support_text_handler

    if not update.message or not update.message.text:
        return

    if not is_admin(update.effective_user.id):
        # مستخدم عادي — أحِل للـ support handler
        await support_text_handler(update, context)
        return

    from helpers import get_state
    text = update.message.text.strip()

    # ─── إدارة أقسام idea6 ────────────────────────────────────────────────
    if get_state("sections_pending_uid") == "1":
        set_state("sections_pending_uid", "0")
        if not text.isdigit():
            await update.message.reply_text("❌ المعرّف غير صحيح. أرسل رقماً فقط.")
            return
        uid = int(text)
        row = db_fetchone("SELECT first_name, username FROM users WHERE user_id=?", (uid,))
        if not row:
            await update.message.reply_text(f"❌ لا يوجد مستخدم بالمعرّف {uid} في قاعدة البيانات.")
            return
        name = row[0] or row[1] or str(uid)
        has_access = has_idea6_access(uid)
        await update.message.reply_text(
            f"👤 المستخدم: {name} ({uid})\n"
            f"📌 وصوله لقسم التحليل الفني الاحترافي: {'مفتوح ✅' if has_access else 'مغلق 🔒'}",
            reply_markup=idea6_access_keyboard(uid, has_access)
        )
        return

    # ─── إعلان broadcast ──────────────────────────────────────────────────
    if get_state("broadcast_pending") == "1":
        set_state("broadcast_pending", "0")
        rows = db_fetchall("SELECT user_id FROM users WHERE payment_status='approved'")
        sent = 0
        for row in rows:
            try:
                await context.bot.send_message(row[0], f"📢 إعلان جديد\n\n{text}")
                sent += 1
            except Exception as e:
                logger.warning("Broadcast failed for user %s: %s", row[0], e)
        await update.message.reply_text(f"✅ تم إرسال الإعلان إلى {sent} مستخدم.")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("استخدم الأمر هكذا:\n/broadcast نص الرسالة")
        return

    message = " ".join(context.args)
    rows = db_fetchall("SELECT user_id FROM users WHERE payment_status='approved'")
    sent = 0
    for row in rows:
        try:
            await context.bot.send_message(row[0], f"📢 إعلان جديد\n\n{message}")
            sent += 1
        except Exception as e:
            logger.warning("Broadcast failed for user %s: %s", row[0], e)

    await update.message.reply_text(f"✅ تم إرسال الإعلان إلى {sent} مستخدم.")
