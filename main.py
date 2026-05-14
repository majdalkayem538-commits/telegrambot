import logging
import threading

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import TOKEN
from database import init_db
from handlers_content import (
    start, menu_router, payment, paid, receive_proof, review_payment,
    approve, reject, library, ideas, progress, continue_last, whats_new,
    videos, support_text_handler,
)
from handlers_admin import admin_panel, admin_router, stats, sales, broadcast
from server import run_web_server

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── التحقق من المتغيرات ──────────────────────────────────────────────────────
if not TOKEN:
    raise ValueError("❌ TOKEN غير موجود! أضفه في Render → Environment Variables")

# ─── تهيئة قاعدة البيانات ─────────────────────────────────────────────────────
init_db()
logger.info("Database initialized ✓")

# ─── بناء التطبيق ─────────────────────────────────────────────────────────────
app = ApplicationBuilder().token(TOKEN).build()

# أوامر نصية
app.add_handler(CommandHandler("start",     start))
app.add_handler(CommandHandler("admin",     admin_panel))
app.add_handler(CommandHandler("stats",     stats))
app.add_handler(CommandHandler("sales",     sales))
app.add_handler(CommandHandler("broadcast", broadcast))

# Callback queries
app.add_handler(CallbackQueryHandler(admin_router,    pattern="^admin_"))
app.add_handler(CallbackQueryHandler(menu_router,     pattern="^menu_"))
app.add_handler(CallbackQueryHandler(payment,         pattern="^pay_"))
app.add_handler(CallbackQueryHandler(paid,            pattern="^paid$"))
app.add_handler(CallbackQueryHandler(review_payment,  pattern="^review_"))
app.add_handler(CallbackQueryHandler(approve,         pattern="^approve_"))
app.add_handler(CallbackQueryHandler(reject,          pattern="^reject_"))
app.add_handler(CallbackQueryHandler(library,         pattern="^library$"))
app.add_handler(CallbackQueryHandler(ideas,           pattern="^idea"))
app.add_handler(CallbackQueryHandler(progress,        pattern="^progress$"))
app.add_handler(CallbackQueryHandler(continue_last,   pattern="^continue_last$"))
app.add_handler(CallbackQueryHandler(whats_new,       pattern="^whats_new$"))
app.add_handler(CallbackQueryHandler(videos,          pattern="^video"))

# رسائل نصية وصور
app.add_handler(MessageHandler(filters.PHOTO,                  receive_proof))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, support_text_handler))

# ─── تشغيل الـ web server في خلفية ──────────────────────────────────────────
threading.Thread(target=run_web_server, daemon=True).start()

logger.info("Bot starting...")
app.run_polling(drop_pending_updates=True)
