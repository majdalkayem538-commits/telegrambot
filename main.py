import threading
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import TOKEN
from handlers_content import (
    start, menu_router, payment, paid, receive_proof, review_payment,
    approve, reject, library, ideas, progress, continue_last, whats_new,
    videos, support_text_handler
)
from handlers_admin import admin_panel, admin_router, stats, sales, broadcast
from server import run_web_server

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
app.add_handler(CallbackQueryHandler(review_payment, pattern="^review_"))
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

threading.Thread(target=run_web_server, daemon=True).start()

print("Bot Running...")
app.run_polling()
