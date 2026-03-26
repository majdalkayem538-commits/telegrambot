import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID, PAYMENT_TEXTS, FAQ_TEXT, COURSE_OVERVIEW_TEXT, VIDEO_CATALOG, TOTAL_VIDEOS, COURSE_PRICE
from database import cursor, conn
from helpers import (
    ensure_user, get_user_approved, get_payment_label, generate_order_id,
    now_str, find_video, progress_bar, is_admin, get_state, set_state
)
from keyboards import main_menu_keyboard, payment_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username, user.first_name)
    paid = get_user_approved(user.id)
    welcome_text = """السلام عليكم و رحمة الله و بركاته🙋🏻‍♂️

💎 اهلاً بكم في بوت Economy Trader 💎

هنا سوف نكون معكم لتعليم التداول من البداية حتى الاحتراف 💱🥇

سعر الكورس هو 25$ أو ما يعادلها بالليرة السورية 💲

اختر من القائمة الرئيسية 👇"""
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(paid))

async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user = query.from_user; ensure_user(user.id, user.username, user.first_name); paid = get_user_approved(user.id)
    if query.data == "menu_home":
        await query.message.reply_text("🏠 القائمة الرئيسية:", reply_markup=main_menu_keyboard(paid)); return
    if query.data == "menu_course":
        await query.message.reply_text(COURSE_OVERVIEW_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 شراء الكورس", callback_data="menu_buy")],[InlineKeyboardButton("🏠 رجوع للقائمة الرئيسية", callback_data="menu_home")]])); return
    if query.data == "menu_buy":
        await query.message.reply_text("💳 اختر طريقة الدفع المناسبة:", reply_markup=payment_keyboard()); return
    if query.data == "menu_faq":
        await query.message.reply_text(FAQ_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 رجوع للقائمة الرئيسية", callback_data="menu_home")]])); return
    if query.data == "menu_support":
        cursor.execute("UPDATE users SET support_pending=1 WHERE user_id=?", (user.id,)); conn.commit()
        await query.message.reply_text("📩 اكتب رسالتك الآن وسيتم إرسالها إلى الدعم مباشرة."); return

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    method = query.data; text = PAYMENT_TEXTS.get(method, "راسل الأدمن لمعرفة طريقة الدفع.")
    cursor.execute("SELECT payment_status, order_id FROM users WHERE user_id=?", (query.from_user.id,)); row = cursor.fetchone()
    current_status = row[0] if row else "none"; existing_order_id = row[1] if row else None
    if current_status in ("pending", "reviewing"):
        await query.message.reply_text(f"⏳ لديك طلب قيد المراجعة بالفعل.\n🧾 رقم الطلب: {existing_order_id if existing_order_id else '-'}"); return
    order_id = generate_order_id()
    cursor.execute("UPDATE users SET selected_payment=?, order_id=? WHERE user_id=?", (method, order_id, query.from_user.id)); conn.commit()
    keyboard = [[InlineKeyboardButton("✅ أرسلت الدفع", callback_data="paid")],[InlineKeyboardButton("⬅️ رجوع", callback_data="menu_buy")]]
    await query.edit_message_text(f"{text}\n\n🧾 رقم طلبك: {order_id}\n\nبعد الدفع اضغط أرسلت الدفع وأرسل صورة إشعار الدفع.", reply_markup=InlineKeyboardMarkup(keyboard))

async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    await query.message.reply_text("📸 أرسل صورة إشعار الدفع الآن.\n\n⚠️ يجب أن تكون صورة واضحة وحديثة.")

async def receive_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; ensure_user(user.id, user.username, user.first_name)
    cursor.execute("SELECT support_pending FROM users WHERE user_id=?", (user.id,)); row = cursor.fetchone(); support_pending = bool(row and row[0] == 1)
    if support_pending and update.message.text:
        await context.bot.send_message(ADMIN_ID, f"📩 رسالة دعم جديدة\n\n👤 المستخدم: {user.first_name}\n🆔 ID: {user.id}\n👤 Username: @{user.username if user.username else 'بدون'}\n\n📝 الرسالة:\n{update.message.text}")
        cursor.execute("UPDATE users SET support_pending=0 WHERE user_id=?", (user.id,)); conn.commit(); await update.message.reply_text("✅ تم إرسال رسالتك إلى الدعم."); return
    if not update.message.photo:
        return
    cursor.execute("SELECT payment_status, order_id, selected_payment FROM users WHERE user_id=?", (user.id,)); status_row = cursor.fetchone()
    current_status = status_row[0] if status_row else "none"; current_order_id = status_row[1] if status_row else None; selected_payment = status_row[2] if status_row else None
    if current_status in ("pending", "reviewing"):
        await update.message.reply_text(f"⏳ لديك طلب قيد المراجعة بالفعل.\n🧾 رقم الطلب: {current_order_id if current_order_id else '-'}"); return
    message_time = update.message.date.timestamp(); current_time = time.time()
    if current_time - message_time > 120:
        await update.message.reply_text("❌ يرجى إرسال صورة إشعار جديدة من الكاميرا."); return
    photo = update.message.photo[-1].file_id; order_id = current_order_id if current_order_id else generate_order_id(); payment_method = get_payment_label(selected_payment)
    cursor.execute("UPDATE users SET proof_message_id=?, payment_status='pending', request_at=?, order_id=? WHERE user_id=?", (update.message.message_id, now_str(), order_id, user.id)); conn.commit()
    keyboard = [[InlineKeyboardButton("👁 بدء المراجعة", callback_data=f"review_{user.id}")],[InlineKeyboardButton("✅ قبول الدفع", callback_data=f"approve_{user.id}")],[InlineKeyboardButton("❌ رفض الدفع", callback_data=f"reject_{user.id}")]]
    sent = await context.bot.send_photo(ADMIN_ID, photo=photo, caption=f"📥 طلب دفع جديد\n\n🧾 رقم الطلب: {order_id}\n👤 المستخدم: {user.first_name}\n🆔 ID: {user.id}\n👤 Username: @{user.username if user.username else 'بدون'}\n💳 طريقة الدفع: {payment_method}\n📌 الحالة: pending", reply_markup=InlineKeyboardMarkup(keyboard))
    cursor.execute("UPDATE users SET admin_message_id=? WHERE user_id=?", (sent.message_id, user.id)); conn.commit()
    await update.message.reply_text(f"✅ تم إرسال الإشعار للمراجعة.\n🧾 رقم طلبك: {order_id}")

async def review_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("غير مسموح", show_alert=True); return
    user_id = int(query.data.split("_")[1])
    cursor.execute("SELECT order_id, selected_payment FROM users WHERE user_id=?", (user_id,)); row = cursor.fetchone(); order_id = row[0] if row else "غير معروف"; selected_payment = row[1] if row else None
    cursor.execute("UPDATE users SET payment_status='reviewing' WHERE user_id=?", (user_id,)); conn.commit()
    await query.edit_message_caption(caption=f"📥 طلب دفع قيد المراجعة\n\n🧾 رقم الطلب: {order_id}\n🆔 ID: {user_id}\n💳 طريقة الدفع: {get_payment_label(selected_payment)}\n📌 الحالة: reviewing", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ قبول الدفع", callback_data=f"approve_{user_id}")],[InlineKeyboardButton("❌ رفض الدفع", callback_data=f"reject_{user_id}")]]))

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("غير مسموح", show_alert=True); return
    user_id = int(query.data.split("_")[1])
    user = await context.bot.get_chat(user_id); name = user.first_name; username_text = f"@{user.username}" if user.username else "لا يوجد"
    cursor.execute("SELECT proof_message_id, selected_payment, order_id, admin_message_id FROM users WHERE user_id=?", (user_id,)); row = cursor.fetchone()
    proof_message_id = row[0] if row else None; selected_payment = row[1] if row else None; order_id = row[2] if row else "غير معروف"; admin_message_id = row[3] if row else None
    approved_at = now_str()
    cursor.execute("UPDATE users SET payment_status='approved', approved_at=? WHERE user_id=?", (approved_at, user_id))
    cursor.execute("INSERT INTO sales (user_id, order_id, payment_method, amount, status, approved_at) VALUES (?, ?, ?, ?, ?, ?)", (user_id, order_id, get_payment_label(selected_payment), COURSE_PRICE, "approved", approved_at)); conn.commit()
    if proof_message_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=proof_message_id)
        except Exception:
            pass
    await context.bot.send_message(user_id, f"🎉 تم تأكيد الدفع بنجاح!\n\n🧾 رقم الطلب: {order_id}\n\n🚀 صار عندك وصول كامل للكورس!", reply_markup=main_menu_keyboard(True))
    try:
        if admin_message_id:
            await context.bot.delete_message(chat_id=ADMIN_ID, message_id=admin_message_id)
        else:
            await query.message.delete()
    except Exception:
        pass
    await context.bot.send_message(ADMIN_ID, f"✅ تم قبول الدفع\n\n🧾 رقم الطلب: {order_id}\n👤 الاسم: {name}\n🔗 اليوزر: {username_text}\n🆔 ID: {user_id}\n💳 الطريقة: {get_payment_label(selected_payment)}")

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("غير مسموح", show_alert=True); return
    user_id = int(query.data.split("_")[1])
    user = await context.bot.get_chat(user_id); name = user.first_name; username_text = f"@{user.username}" if user.username else "لا يوجد"
    cursor.execute("SELECT selected_payment, order_id, admin_message_id FROM users WHERE user_id=?", (user_id,)); row = cursor.fetchone(); selected_payment = row[0] if row else None; order_id = row[1] if row else "غير معروف"; admin_message_id = row[2] if row else None
    cursor.execute("UPDATE users SET payment_status='rejected' WHERE user_id=?", (user_id,))
    cursor.execute("INSERT INTO sales (user_id, order_id, payment_method, amount, status, approved_at) VALUES (?, ?, ?, ?, ?, ?)", (user_id, order_id, get_payment_label(selected_payment), COURSE_PRICE, "rejected", now_str())); conn.commit()
    await context.bot.send_message(user_id, f"❌ تم رفض إشعار الدفع.\n\n🧾 رقم الطلب: {order_id}\nيرجى إرسال صورة أوضح لإثبات الدفع.")
    try:
        if admin_message_id:
            await context.bot.delete_message(chat_id=ADMIN_ID, message_id=admin_message_id)
        else:
            await query.message.delete()
    except Exception:
        pass
    await context.bot.send_message(ADMIN_ID, f"❌ تم رفض الدفع\n\n🧾 رقم الطلب: {order_id}\n👤 الاسم: {name}\n🔗 اليوزر: {username_text}\n🆔 ID: {user_id}\n💳 الطريقة: {get_payment_label(selected_payment)}\n📎 الإشعار غير صحيح")

async def library(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ لازم تدفع أول شي لتدخل المكتبة", reply_markup=main_menu_keyboard(False)); return
    keyboard = [[InlineKeyboardButton(section["title"], callback_data=section_key)] for section_key, section in VIDEO_CATALOG.items()]
    keyboard += [[InlineKeyboardButton("📊 تقدمي في الكورس", callback_data="progress")],[InlineKeyboardButton("▶️ أكمل من آخر درس", callback_data="continue_last")],[InlineKeyboardButton("🆕 ما الجديد", callback_data="whats_new")],[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="menu_home")]]
    await query.message.reply_text("📚 مكتبة الفيديوهات\n\nاختر القسم الذي تريد البدء به:", reply_markup=InlineKeyboardMarkup(keyboard))

async def ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ لا يمكنك دخول هذا القسم قبل تأكيد الدفع."); return
    section = VIDEO_CATALOG.get(query.data)
    if not section: return
    keyboard = []
    for video in section["videos"]:
        label = video["title"] + (" 🆕" if video["is_new"] else "")
        keyboard.append([InlineKeyboardButton(label, callback_data=video["key"])])
    keyboard.append([InlineKeyboardButton("⬅️ رجوع إلى المكتبة", callback_data="library")])
    await query.message.reply_text(f"{section['title']}\n\n{section['description']}\n\nاختر الفيديو:", reply_markup=InlineKeyboardMarkup(keyboard))

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ لا يمكنك مشاهدة التقدم قبل تأكيد الدفع."); return
    cursor.execute("SELECT COUNT(*) FROM watched WHERE user_id=?", (query.from_user.id,)); watched_count = cursor.fetchone()[0]
    percent = int((watched_count / TOTAL_VIDEOS) * 100) if TOTAL_VIDEOS > 0 else 0
    await query.message.reply_text(f"📊 تقدمك في الكورس\n\n{progress_bar(watched_count, TOTAL_VIDEOS)} {percent}%\n\n🎥 الفيديوهات التي شاهدتها: {watched_count}/{TOTAL_VIDEOS}")

async def continue_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ يجب تأكيد الدفع أولاً."); return
    cursor.execute("SELECT last_video_key FROM users WHERE user_id=?", (query.from_user.id,)); row = cursor.fetchone(); last_video_key = row[0] if row else None
    if not last_video_key:
        await query.message.reply_text("ℹ️ لم تشاهد أي فيديو بعد. ابدأ من المكتبة."); return
    _, section, video = find_video(last_video_key)
    if not video:
        await query.message.reply_text("⚠️ آخر فيديو غير موجود حالياً."); return
    if "PLACEHOLDER" in video["file_id"]:
        await query.message.reply_text("⚠️ هذا الفيديو لم يتم رفعه بعد."); return
    await context.bot.send_message(query.from_user.id, f"▶️ آخر درس وصلت له:\n{section['title']} - {video['title']}")
    await context.bot.send_video(chat_id=query.from_user.id, video=video["file_id"], protect_content=True)

async def whats_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ يجب تأكيد الدفع أولاً."); return
    watched_keys = set(); cursor.execute("SELECT video_key FROM watched WHERE user_id=?", (query.from_user.id,))
    for row in cursor.fetchall(): watched_keys.add(row[0])
    lines = []
    for section in VIDEO_CATALOG.values():
        for video in section["videos"]:
            if video["is_new"] and video["key"] not in watched_keys:
                lines.append(f"🆕 {section['title']} - {video['title']}")
    if not lines:
        await query.message.reply_text("لا يوجد دروس جديدة غير مشاهدة حالياً."); return
    await query.message.reply_text("🆕 الدروس الجديدة:\n\n" + "\n".join(lines))

async def videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if not get_user_approved(query.from_user.id):
        await query.message.reply_text("❌ لا يمكنك مشاهدة الفيديو قبل تأكيد الدفع."); return
    _, _, video = find_video(query.data)
    if not video: return
    file_id = video["file_id"]
    if not file_id or "PLACEHOLDER" in file_id:
        await query.message.reply_text("⚠️ هذا الفيديو لم يتم رفعه بعد."); return
    cursor.execute("INSERT OR IGNORE INTO watched (user_id, video_key, watched_at) VALUES (?, ?, ?)", (query.from_user.id, query.data, now_str()))
    cursor.execute("UPDATE users SET last_video_key=? WHERE user_id=?", (query.data, query.from_user.id)); conn.commit()
    await context.bot.send_video(chat_id=query.from_user.id, video=file_id, protect_content=True)

async def support_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user = update.effective_user; ensure_user(user.id, user.username, user.first_name)
    if is_admin(user.id) and get_state("broadcast_pending") == "1":
        message = update.message.text
        cursor.execute("SELECT user_id FROM users WHERE payment_status='approved'"); users = [row[0] for row in cursor.fetchall()]
        sent = 0
        for user_id in users:
            try:
                await context.bot.send_message(user_id, f"📢 إعلان جديد\n\n{message}"); sent += 1
            except Exception:
                pass
        set_state("broadcast_pending", "0")
        await update.message.reply_text(f"✅ تم إرسال الإعلان إلى {sent} مستخدم."); return
    cursor.execute("SELECT support_pending FROM users WHERE user_id=?", (user.id,)); row = cursor.fetchone(); support_pending = bool(row and row[0] == 1)
    if not support_pending: return
    await context.bot.send_message(ADMIN_ID, f"📩 رسالة دعم جديدة\n\n👤 المستخدم: {user.first_name}\n🆔 ID: {user.id}\n👤 Username: @{user.username if user.username else 'بدون'}\n\n📝 الرسالة:\n{update.message.text}")
    cursor.execute("UPDATE users SET support_pending=0 WHERE user_id=?", (user.id,)); conn.commit()
    await update.message.reply_text("✅ تم إرسال رسالتك إلى الدعم.")
