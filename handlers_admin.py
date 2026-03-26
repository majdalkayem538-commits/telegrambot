import os
import pandas as pd
from datetime import datetime
from openpyxl import Workbook
from telegram import Update
from telegram.ext import ContextTypes
from database import cursor, conn
from helpers import is_admin, set_state, get_payment_label
from keyboards import admin_panel_keyboard


def export_sales_to_excel():
    cursor.execute("""
        SELECT user_id, order_id, payment_method, amount, status, approved_at
        FROM sales
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()

    columns = [
        "User ID",
        "Order ID",
        "Payment Method",
        "Amount",
        "Status",
        "Approved At"
    ]

    df = pd.DataFrame(rows, columns=columns)

    os.makedirs("exports", exist_ok=True)
    filename = f"exports/sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    df.to_excel(filename, index=False, engine="xlsxwriter")

    return filename

def get_total_profit():
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM sales
        WHERE status='approved'
    """)
    return cursor.fetchone()[0]

def get_total_sales_count():
    cursor.execute("""
        SELECT COUNT(*)
        FROM sales
        WHERE status='approved'
    """)
    return cursor.fetchone()[0]

def get_today_profit():
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM sales
        WHERE status='approved'
        AND date(substr(approved_at, 1, 10)) = date('now')
    """)
    return cursor.fetchone()[0]

def get_today_sales_count():
    cursor.execute("""
        SELECT COUNT(*)
        FROM sales
        WHERE status='approved'
        AND date(substr(approved_at, 1, 10)) = date('now')
    """)
    return cursor.fetchone()[0]

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        await update.message.reply_text("🛠 لوحة الأدمن", reply_markup=admin_panel_keyboard())

async def admin_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("غير مسموح", show_alert=True)
        return

    if query.data == "admin_stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE payment_status='approved'")
        paid_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sales WHERE status='approved'")
        sales_count = cursor.fetchone()[0]

        total_profit = get_total_profit()

        cursor.execute("SELECT COUNT(*) FROM watched")
        watched_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE payment_status IN ('pending', 'reviewing')")
        pending_count = cursor.fetchone()[0]

        await query.message.reply_text(
            f"📊 إحصائيات البوت\n\n"
            f"👥 عدد المستخدمين: {total_users}\n"
            f"💰 عدد المشترين: {paid_users}\n"
            f"🧾 عدد العمليات المقبولة: {sales_count}\n"
            f"📥 عدد الطلبات المعلقة: {pending_count}\n"
            f"💵 إجمالي الأرباح: {total_profit}$\n"
            f"🎥 عدد المشاهدات المسجلة: {watched_count}"
        )
        return

    if query.data == "admin_sales":
        cursor.execute("""
            SELECT user_id, order_id, payment_method, amount, status, approved_at
            FROM sales
            ORDER BY id DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()

        if not rows:
            await query.message.reply_text("لا توجد عمليات مسجلة بعد.")
            return

        lines = ["💰 آخر 10 عمليات:\n"]
        for row in rows:
            lines.append(
                f"👤 {row[0]} | 🧾 {row[1]} | 💳 {row[2]} | 💵 {row[3]}$ | 📌 {row[4]} | 🕒 {row[5]}"
            )

        await query.message.reply_text("\n".join(lines))
        return

    if query.data == "admin_pending":
        cursor.execute("""
            SELECT user_id, order_id, selected_payment, request_at, payment_status
            FROM users
            WHERE payment_status IN ('pending', 'reviewing')
            ORDER BY request_at DESC
        """)
        rows = cursor.fetchall()

        if not rows:
            await query.message.reply_text("لا توجد طلبات معلقة حالياً.")
            return

        lines = ["📥 الطلبات المعلقة:\n"]
        for row in rows:
            lines.append(
                f"🧾 {row[1] if row[1] else '-'} | 👤 {row[0]} | 💳 {get_payment_label(row[2])} | 📌 {row[4]} | 🕒 {row[3]}"
            )

        await query.message.reply_text("\n".join(lines))
        return

    if query.data == "admin_users":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE payment_status='approved'")
        paid_users = cursor.fetchone()[0]

        await query.message.reply_text(
            f"👥 المستخدمون\n\n"
            f"إجمالي المستخدمين: {total_users}\n"
            f"المستخدمون الدافعون: {paid_users}"
        )
        return

    if query.data == "admin_export_excel":
        file_path = export_sales_to_excel()

        with open(file_path, "rb") as f:
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=f,
                filename=os.path.basename(file_path),
                caption="📁 تم تصدير العمليات إلى ملف Excel"
            )
        return

    if query.data == "admin_profit":
        total_profit = get_total_profit()
        total_sales = get_total_sales_count()
        today_profit = get_today_profit()
        today_sales = get_today_sales_count()

        await query.message.reply_text(
            f"💰 تقرير الأرباح\n\n"
            f"📈 إجمالي الأرباح: {total_profit}$\n"
            f"🧾 إجمالي العمليات المقبولة: {total_sales}\n\n"
            f"📅 أرباح اليوم: {today_profit}$\n"
            f"✅ عمليات اليوم المقبولة: {today_sales}"
        )
        return

    if query.data == "admin_broadcast":
        set_state("broadcast_pending", "1")
        await query.message.reply_text("📢 أرسل الآن نص الإعلان الذي تريد إرساله لكل المشتركين.")
        return

    if query.data == "admin_back":
        await query.message.reply_text("🏠 رجعت من لوحة الأدمن.")
        return

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE payment_status='approved'")
    paid_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sales WHERE status='approved'")
    sales_count = cursor.fetchone()[0]

    total_profit = get_total_profit()

    cursor.execute("SELECT COUNT(*) FROM watched")
    watched_count = cursor.fetchone()[0]

    await update.message.reply_text(
        f"📊 إحصائيات البوت\n\n"
        f"👥 عدد المستخدمين: {total_users}\n"
        f"💰 عدد المشترين: {paid_users}\n"
        f"🧾 عدد العمليات المقبولة: {sales_count}\n"
        f"💵 إجمالي الأرباح: {total_profit}$\n"
        f"🎥 عدد المشاهدات المسجلة: {watched_count}"
    )

async def sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    cursor.execute("""
        SELECT user_id, order_id, payment_method, amount, status, approved_at
        FROM sales
        ORDER BY id DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("لا توجد عمليات مسجلة بعد.")
        return

    lines = ["💰 آخر 10 عمليات:\n"]
    for row in rows:
        lines.append(
            f"👤 {row[0]} | 🧾 {row[1]} | 💳 {row[2]} | 💵 {row[3]}$ | 📌 {row[4]} | 🕒 {row[5]}"
        )

    await update.message.reply_text("\n".join(lines))

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("استخدم الأمر هكذا:\n/broadcast نص الرسالة")
        return

    message = " ".join(context.args)

    cursor.execute("SELECT user_id FROM users WHERE payment_status='approved'")
    users = [row[0] for row in cursor.fetchall()]

    sent = 0
    for user_id in users:
        try:
            await context.bot.send_message(user_id, f"📢 إعلان جديد\n\n{message}")
            sent += 1
        except Exception:
            pass

    await update.message.reply_text(f"✅ تم إرسال الإعلان إلى {sent} مستخدم.")
