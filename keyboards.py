from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard(is_paid: bool):
    keyboard = [[InlineKeyboardButton("▶️ ستارت", callback_data="menu_home")],[InlineKeyboardButton("💳 شراء الكورس", callback_data="menu_buy")],[InlineKeyboardButton("❓ الأسئلة الشائعة", callback_data="menu_faq")],[InlineKeyboardButton("📩 الدعم", callback_data="menu_support")]]
    if is_paid:
        keyboard.insert(1, [InlineKeyboardButton("📚 مكتبة الفيديوهات", callback_data="library")])
    return InlineKeyboardMarkup(keyboard)

def payment_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("USDT", callback_data="pay_usdt")],[InlineKeyboardButton("سيريتل كاش", callback_data="pay_syriatel")],[InlineKeyboardButton("شام كاش", callback_data="pay_sham")],[InlineKeyboardButton("تحويل بنكي", callback_data="pay_bank")],[InlineKeyboardButton("حوالة نقدية", callback_data="pay_cash")],[InlineKeyboardButton("⬅️ رجوع للقائمة الرئيسية", callback_data="menu_home")]])

def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("💰 آخر العمليات", callback_data="admin_sales")],
        [InlineKeyboardButton("📥 الطلبات المعلقة", callback_data="admin_pending")],
        [InlineKeyboardButton("👥 عدد المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("📁 تصدير Excel", callback_data="admin_export_excel")],
        [InlineKeyboardButton("💰 تقرير الأرباح", callback_data="admin_profit")],
        [InlineKeyboardButton("📢 إرسال إعلان", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🏠 رجوع", callback_data="admin_back")],
    ])
