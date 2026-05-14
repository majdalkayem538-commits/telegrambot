import os
import logging
import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import COURSE_PRICE
from database import db_execute, db_fetchone, db_fetchall
from helpers import is_admin, set_state, get_payment_label
from keyboards import admin_panel_keyboard

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
