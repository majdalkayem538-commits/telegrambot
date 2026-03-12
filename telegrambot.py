import sqlite3
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8439272696:AAHDPkJ9WczVYhT6zrIvPLPimXZmOol1s6M"
ADMIN_ID = 728810082

# -------- DATABASE --------

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
approved INTEGER DEFAULT 0
)
""")

conn.commit()

# -------- START --------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    keyboard = [
        [InlineKeyboardButton("USDT", callback_data="pay_usdt")],
        [InlineKeyboardButton("سيريتل كاش", callback_data="pay_syriatel")],
        [InlineKeyboardButton("شام كاش", callback_data="pay_sham")],
        [InlineKeyboardButton("تحويل بنكي", callback_data="pay_bank")],
        [InlineKeyboardButton("حوالة نقدية", callback_data="pay_cash")]
    ]

    await update.message.reply_text(
        """السلام عليكم و رحمة الله و بركاته🙋🏻‍♂️

    💎اهلا بكم في بوت Economy Trader 💎

    هنا سوف نكون معكم لتعليم التداول من البداية حتى الاحتراف💱🥇

    سعر الكورس هو 25 $ او ما يعادلها بالليرة السورية 💲

    
    المهارات التي سوف تتعلمها بعد اخذ الكورس📚
1️⃣ المصطلحات الاساسية في علم التداول 📃 
2️⃣التحليل الاساسي🏛️
3️⃣التحليل الفني👨🏻‍💻
4️⃣الشموع اليابانية📊


 للمتابعة يرجى اختيار طريقة دفع من الطرق الموضحة ادناه👇🏻⬇️
    """,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------- PAYMENT --------

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    method = query.data

    if method == "pay_usdt":
        text = """
💳 الدفع عبر USDT

BEP20:
0xDBbD77bF4aD00576F66EB8be244E278B813cA8Db

TRC20:
TW15xXADYSPytvCsoGxA9Z988h35HpJtrN
"""

    elif method == "pay_syriatel":
        text = """
💰 الدفع عبر سيريتل كاش

الرقم:
31623094
"""

    elif method == "pay_sham":
        text = """
💎 الدفع عبر شام كاش

المعرف:
4d0c06e319a22353274375a58987f44b

اسم الحساب:
مجد غسان القيم
"""

    elif method == "pay_bank":
        text = """
🏦 تحويل بنكي

IBAN:
بنك البركة
1270444
"""

    elif method == "pay_cash":
        text = """
💵 حوالة نقدية

الاسم:
مجد غسان القيم
الهاتف:
0937872522
"""

    else:
        text = "راسل الأدمن لمعرفة طريقة الدفع."

    keyboard = [
        [InlineKeyboardButton("✅ أرسلت الدفع", callback_data="paid")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_payment")]
    ]

    await query.edit_message_text(
        text + "\n\nبعد الدفع اضغط أرسلت الدفع وأرسل صورة إشعار الدفع.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------- BACK --------

async def back_to_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("USDT", callback_data="pay_usdt")],
        [InlineKeyboardButton("سيريتل كاش", callback_data="pay_syriatel")],
        [InlineKeyboardButton("شام كاش", callback_data="pay_sham")],
        [InlineKeyboardButton("تحويل بنكي", callback_data="pay_bank")],
        [InlineKeyboardButton("حوالة نقدية", callback_data="pay_cash")]
    ]

    await query.edit_message_text(
        "اختر طريقة الدفع:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------- PAID --------

async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text("📸 أرسل صورة إشعار الدفع الآن.")

# -------- RECEIVE PROOF --------

async def receive_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    message_time = update.message.date.timestamp()
    current_time = time.time()

    if current_time - message_time > 120:
        await update.message.reply_text(
            "❌ يرجى إرسال صورة إشعار جديدة من الكاميرا."
        )
        return

    photo = update.message.photo[-1].file_id

    keyboard = [
        [InlineKeyboardButton("✅ تم الدفع", callback_data=f"approve_{user.id}")],
        [InlineKeyboardButton("❌ رفض الدفع", callback_data=f"reject_{user.id}")]
    ]

    await context.bot.send_photo(
        ADMIN_ID,
        photo=photo,
        caption=f"إثبات دفع جديد\n\nالمستخدم: {user.first_name}\nID: {user.id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("✅ تم إرسال الإشعار للمراجعة.")

# -------- APPROVE --------

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    cursor.execute("UPDATE users SET approved=1 WHERE user_id=?", (user_id,))
    conn.commit()

    keyboard = [
        [InlineKeyboardButton("📚 دخول مكتبة الفيديوهات", callback_data="library")]
    ]

    await context.bot.send_message(
        user_id,
        "✅ تم تأكيد الدفع.\nيمكنك الآن الدخول إلى مكتبة الفيديوهات.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------- REJECT --------

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    await context.bot.send_message(
        user_id,
        "❌ تم رفض إشعار الدفع.\nيرجى إرسال إشعار صحيح."
    )

    await query.edit_message_text("تم رفض الدفع.")

# -------- LIBRARY --------

async def library(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("📚 المصطلحات الاساسية", callback_data="idea1")],
        [InlineKeyboardButton("📚 التحليل الاساسي", callback_data="idea2")],
        [InlineKeyboardButton("📚 التحليل الفني", callback_data="idea3")],
        [InlineKeyboardButton("📚 الشموع اليابانية", callback_data="idea4")]
    ]

    await query.message.reply_text(
        "اختر الفكرة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------- IDEAS --------

async def ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🎥 فيديو 1", callback_data="video1")],
        [InlineKeyboardButton("🎥 فيديو 2", callback_data="video2")],
        [InlineKeyboardButton("🎥 فيديو 3", callback_data="video3")]
    ]

    await query.message.reply_text(
        "اختر الفيديو:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# -------- VIDEO --------

async def videos(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await context.bot.send_video(
        chat_id=query.from_user.id,
        video="VIDEO_FILE_ID",
        protect_content=True
    )

# -------- MAIN --------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(payment, pattern="pay_"))
app.add_handler(CallbackQueryHandler(back_to_payment, pattern="back_to_payment"))
app.add_handler(CallbackQueryHandler(paid, pattern="paid"))
app.add_handler(CallbackQueryHandler(approve, pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject, pattern="reject_"))
app.add_handler(CallbackQueryHandler(library, pattern="library"))
app.add_handler(CallbackQueryHandler(ideas, pattern="idea"))
app.add_handler(CallbackQueryHandler(videos, pattern="video"))
app.add_handler(MessageHandler(filters.PHOTO, receive_proof))

print("Bot Running...")

app.run_polling()