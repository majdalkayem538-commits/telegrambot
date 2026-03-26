import os
import sqlite3
import time
import random
from datetime import datetime, UTC
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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
COURSE_PRICE = 25

VIDEO_CATALOG = {
    "idea1": {
        "title": "📚 المصطلحات الأساسية",
        "description": "في هذا القسم ستتعلم أهم المصطلحات الأساسية في عالم التداول من البداية.",
        "videos": [
            {"key": "video1", "title": "🎥 المقدمة", "file_id": "BAACAgQAAxkBAAIB1Wm5Nx3RNkMTyxUAAWkUzqDhqZoMIAAC5x0AAo_N0VHDkAtlkTRmMToE", "is_new": True},
            {"key": "video2", "title": "🎥 أنواع أسواق المال", "file_id": "BAACAgQAAxkBAAIB3Gm5RrqcetQ7TgO2uliw5JNe1dOPAAL0HQACj83RUeLX2wciEyI9OgQ", "is_new": True},
            {"key": "video3", "title": "🎥 مزايا الفوركس", "file_id": "BAACAgQAAxkBAAIB3mm5R3LRK72GEfs6tyQufoHXbuDrAAL1HQACj83RUVp-0qQi65siOgQ", "is_new": True},
            {"key": "video4", "title": "🎥 العملات المتداولة", "file_id": "BAACAgQAAxkBAAIB4Gm5SEMHvJZsymaAPFZUqzO5uN9vAAL2HQACj83RUcHeEnjE-4OYOgQ", "is_new": False},
            {"key": "video5", "title": "🎥 أزواج العملات", "file_id": "BAACAgQAAxkBAAIB4mm5SNiz2wb21DxintOYIERcP_1YAAL3HQACj83RUeMYWpVcaqa3OgQ", "is_new": False},
            {"key": "video6", "title": "🎥 أحجام العقود", "file_id": "BAACAgQAAxkBAAIB5Gm5Sd5EV2REkKeL6kIsmWKIe9v0AAL4HQACj83RUeub7aNxLd3eOgQ", "is_new": False},
            {"key": "video7", "title": "🎥 النقطة وكيفية حساب الأرباح", "file_id": "BAACAgQAAxkBAAIB5mm5WB7bWK6sYW3AzDeqirdDVPNAAAL_HQACj83RUYXXFb_clCCDOgQ", "is_new": False},
            {"key": "video8", "title": "🎥 الرافعة المالية", "file_id": "BAACAgQAAxkBAAIB6Gm5WGhxcg8yk6kHW742-FCmE2mvAAMeAAKPzdFRDoHyUxiaOYY6BA", "is_new": False},
        ],
    },
    "idea2": {
        "title": "🏛️ التحليل الأساسي",
        "description": "في هذا القسم ستتعلم التحليل الأساسي وتأثير المؤشرات الاقتصادية والسياسية على السوق.",
        "videos": [
            {"key": "video9", "title": "🎥 معنى التحليل الأساسي", "file_id": "BAACAgQAAxkBAAICjWm73uAiJwJr4qvf8H41-C8RiVTHAAJhGwACLajgUQmuNgehSdgHOgQ", "is_new": True},
            {"key": "video10", "title": "🎥 معدل الفائدة وتأثيره - الجزء الأول", "file_id": "BAACAgQAAxkBAAICj2m73urbyrz9eecldDBr6Z8of047AAJiGwACLajgUQNGrX2g6T_bOgQ", "is_new": True},
            {"key": "video11", "title": "🎥 معدل الفائدة وتأثيره - الجزء الثاني", "file_id": "BAACAgQAAxkBAAICkWm73vl0IEtSjf00eI-NQuCok6UpAAJjGwACLajgUSO1MMh6TgqiOgQ", "is_new": False},
            {"key": "video12", "title": "🎥 الناتج المحلي الإجمالي - الجزء الأول", "file_id": "BAACAgQAAxkBAAICk2m73wS6LJeFkihj_lmxQpoO3vwbAAJkGwACLajgUaJi79mIKir4OgQ", "is_new": False},
            {"key": "video13", "title": "🎥 الناتج المحلي الإجمالي - الجزء الثاني", "file_id": "BAACAgQAAxkBAAIClWm73xBCPTELT78uvjlsRXQv0dWyAAJlGwACLajgUTygH8BJqNnCOgQ", "is_new": False},
            {"key": "video14", "title": "🎥 معدل البطالة", "file_id": "BAACAgQAAxkBAAICl2m73x59oktSqTc1-qw9hU5MIHtnAAJmGwACLajgUYvxB_tmO6pVOgQ", "is_new": False},
            {"key": "video15", "title": "🎥 التضخم وأنواعه", "file_id": "BAACAgQAAxkBAAICmWm730i57S1VHqEImO0IOkPmnL8LAAJnGwACLajgURo6b2i0ThAXOgQ", "is_new": False},
            {"key": "video17", "title": "🎥 الأحداث السياسية والتجارة الدولية وتأثيرها", "file_id": "BAACAgQAAxkBAAICm2m8CE6nZ23jWVUkHo01PhSmDYNmAAKLGwACLajgUYjYyYzIGxZZOgQ", "is_new": False},
        ],
    },
    "idea3": {
        "title": "📈 التحليل الفني",
        "description": "في هذا القسم ستتعلم التحليل الفني وأهم الأدوات والمؤشرات والنماذج المستخدمة في قراءة السوق.",
        "videos": [
            {"key": "video18", "title": "🎥 القمم والقيعان", "file_id": "BAACAgQAAxkBAAIC72nC_IFNUSqGAzH4lZxqBKyxstmyAAKSIgACXG8YUixxJz_HjLvnOgQ", "is_new": True},
            {"key": "video19", "title": "🎥شرح القمم و القيعان عملي", "file_id": "BAACAgQAAxkBAAIC8WnDvYdle7szBQAB2posYyKlMSCvpQACnx0AAlxvIFK3NYwMpVFCfjoE", "is_new": True},
            {"key": "video20", "title": "🎥 الاتجاه الصاعد والهابط - شرح نظري", "file_id": "BAACAgQAAxkBAAIC82nDvcjrf4ZftMKtzmu8frDtPPv6AAKgHQACXG8gUrpc7mnMFukQOgQ", "is_new": False},
            {"key": "video21", "title": "🎥 الاتجاه الصاعد والهابط - تطبيق عملي", "file_id": "BAACAgQAAxkBAAIC9WnDvlOBb8OO9CMgeiRYKIxbuzVmAAKhHQACXG8gUnTjy5afMXxHOgQ", "is_new": False},
            {"key": "video22", "title": "🎥 الدعم والمقاومة - شرح نظري", "file_id": "BAACAgQAAxkBAAIC92nDvxwqKrROci7xRQNg1LxqBOsjAAKiHQACXG8gUlsEDChFJxGiOgQ", "is_new": False},
            {"key": "video23", "title": "🎥 الدعم والمقاومة - شرح عملي", "file_id": "BAACAgQAAxkBAAIC-WnDv7cQcoe6r4Mvx2Gv0gRN-gR8AAKjHQACXG8gUhHddYtaLE-NOgQ", "is_new": False},
            {"key": "video24", "title": "🎥 مؤشر RSI", "file_id": "BAACAgQAAxkBAAIC-2nDwCh3qOiNxKtc33DuVcR5ZatYAAKkHQACXG8gUsc7ZRZ9xIRbOgQ", "is_new": False},
            {"key": "video25", "title": "🎥 مؤشر Stochastic", "file_id": "BAACAgQAAxkBAAIC_WnDwJLx_cnbMjN6MbUUPa5FzWWGAAKmHQACXG8gUpARCwgflTjhOgQ", "is_new": False},
            {"key": "video26", "title": "🎥 مؤشر MACD", "file_id": "BAACAgQAAxkBAAIC_2nDwRYM7wEHDeWE4eaBZAiNpEPoAAKnHQACXG8gUgSLZd4kJbVeOgQ", "is_new": False},
            {"key": "video27", "title": "🎥 فيبوناتشي", "file_id": "BAACAgQAAxkBAAIDAWnDwkvslAwh_u5Cy9D7Jb_Syu8bAAKpHQACXG8gUhQG5BYCGuecOgQ", "is_new": False},
            {"key": "video28", "title": "🎥 الفراغات السعرية", "file_id": "BAACAgQAAxkBAAIDA2nDwrLN1Qm7iUJSG5kRAtR3esoYAAKqHQACXG8gUld709CjkYJfOgQ", "is_new": False},
            {"key": "video29", "title": "🎥 النماذج السعرية الكلاسيكية - الجزء الأول", "file_id": "BAACAgQAAxkBAAIDBWnDwya63Z3Mg31CSNBNdIJQi4ROAAKrHQACXG8gUqCYyJd9im1mOgQ", "is_new": False},
            {"key": "video30", "title": "🎥 النماذج السعرية الكلاسيكية - الجزء الثاني", "file_id": "BAACAgQAAxkBAAIDB2nDw7jkqqJ2TB_Yu0r0cNoLvfKWAAKsHQACXG8gUqAXthflhKnMOgQ", "is_new": False},
            {"key": "video31", "title": "🎥 النماذج السعرية الكلاسيكية - الجزء الثالث", "file_id": "BAACAgQAAxkBAAIDCWnDxBBoBBt7vnFdDSuw_kIVOCDZAAKuHQACXG8gUsfkRg3DsPuvOgQ", "is_new": False},
        ],
    },
    "idea4": {
        "title": "🕯️ الشموع اليابانية",
        "description": "في هذا القسم ستتعلم قراءة الشموع اليابانية وأهم النماذج المستخدمة في التحليل.",
        "videos": [
            {"key": "video32", "title": "🎥 مقدمة عن الشموع اليابانية", "file_id": "BAACAgQAAxkBAAIDC2nFUQh_2CCivFW_D3qn7bY8lAONAAJ3IAAChywpUoE9k3MYteQxOgQ", "is_new": True},
            {"key": "video33", "title": "🎥 المطرقة والمطرقة المقلوبة والرجل المشنوق", "file_id": "BAACAgQAAxkBAAIDDWnFURdFxiC3spsx9Q4ZIh9UJt6NAAJ4IAAChywpUtLeSKSrPLO0OgQ", "is_new": True},
            {"key": "video34", "title": "🎥 نجمة الصباح ونجمة المساء", "file_id": "BAACAgQAAxkBAAIDF2nFUVh84TvWiNwBrtwsWPtw3VS8AAJ9IAAChywpUlvyXdltfWvzOgQ", "is_new": False},
            {"key": "video35", "title": "🎥  نموذج الشهاب و شمعة الدوجي ", "file_id": "BAACAgQAAxkBAAIDD2nFUSLbzRprhyXPWVdDvTH4l0RxAAJ5IAAChywpUo43h2z3EXLzOgQ", "is_new": False},
            {"key": "video36", "title": "🎥 الشموع عالية الظلال", "file_id": "BAACAgQAAxkBAAIDEWnFUStsBEzIZ--LdntGYlYh9-KbAAJ6IAAChywpUjoIe5WUbAMSOgQ", "is_new": False},
            {"key": "video37", "title": "🎥 الابتلاع الشرائي والبيعي", "file_id": "BAACAgQAAxkBAAIDE2nFUTpepi9XNYzdh1jPI3Ots4G7AAJ7IAAChywpUro66hQOuuh4OgQ", "is_new": False},
            {"key": "video38", "title": "🎥 السحابة القاتمة والخط الثاقب", "file_id": "BAACAgQAAxkBAAIDFWnFUUiSMidTlwuQytz33wmjGurkAAJ8IAAChywpUjCILJi40j6BOgQ", "is_new": False},
            {"key": "video39", "title": "🎥 الهرامي الشرائي والبيعي", "file_id": "BAACAgQAAxkBAAIDG2nFZKcQFaNeUNDgqFqvDzCczZngAAKDIAAChywpUo1FyAva8tD-OgQ", "is_new": False},
            {"key": "video40", "title": "🎥 النماذج الاستمراية و شمعتي الانعكاس", "file_id": "BAACAgQAAxkBAAIDGWnFUWnR2Mfb7R_0fQwwJRW_na0RAAJ-IAAChywpUuBntuBI4Uv-OgQ", "is_new": False},
        ],
    },
    "idea5": {
        "title": "📚 نصائح للمتداولين",
        "description": "في هذا القسم ستتعلم نصائح مهمة للمتداولين وكيفية إنشاء حساب تجريبي وإدارة رأس المال.",
        "videos": [
            {"key": "video41", "title": "🎥 كيف نعمل حساب و نوثقو على المنصة", "file_id": "BAACAgQAAxkBAAIDH2nFZU_HMZ8YBBE8n47JFAAB3TK5TAAChSAAAocsKVJvT0zvXX0cjDoE", "is_new": True},
            {"key": "video42", "title": "🎥 الخاتمة", "file_id": "BAACAgQAAxkBAAIDHWnFZMy9j4DwXMUnxkpjagkHYDmmAAKEIAAChywpUpu-tAc4JENUOgQ", "is_new": True},
        ],
    },
}

TOTAL_VIDEOS = sum(len(section["videos"]) for section in VIDEO_CATALOG.values())
PAYMENT_TEXTS = {"pay_usdt":"💳 الدفع عبر USDT\n\nBEP20:\n0xDBbD77bF4aD00576F66EB8be244E278B813cA8Db\n\nTRC20:\nTW15xXADYSPytvCsoGxA9Z988h35HpJtrN","pay_syriatel":"💰 الدفع عبر سيريتل كاش\n\nالرقم:\n31623094","pay_sham":"💎 الدفع عبر شام كاش\n\nالمعرف:\n4d0c06e319a22353274375a58987f44b\n\nاسم الحساب:\nمجد غسان القيم","pay_bank":"🏦 تحويل بنكي\n\nIBAN:\nبنك البركة\n1270444","pay_cash":"💵 حوالة نقدية\n\nالاسم:\nمجد غسان القيم\nالهاتف:\n0937872522"}
FAQ_TEXT = "❓ الأسئلة الشائعة\n\n1) هل الوصول إلى الكورس دائم؟\nنعم، الوصول دائم بعد تأكيد الدفع.\n\n2) هل أستطيع مشاهدة الفيديوهات أكثر من مرة؟\nنعم.\n\n3) ماذا أفعل إذا تم رفض إشعار الدفع؟\nأرسل صورة أوضح لإشعار الدفع ثم أعد المحاولة.\n\n4) هل يمكن إعادة توجيه الفيديوهات؟\nلا، الفيديوهات محمية داخل البوت."
COURSE_OVERVIEW_TEXT = "📘 محتوى الكورس\n\n1️⃣ المصطلحات الأساسية\n2️⃣ التحليل الأساسي\n3️⃣ التحليل الفني\n4️⃣ الشموع اليابانية\n5️⃣ نصائح للمتداولين\n\n💲 سعر الكورس: 25$"
