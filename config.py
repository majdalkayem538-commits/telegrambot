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
            {"key": "video18", "title": "🎥 القمم والقيعان", "file_id": "PLACEHOLDER_VIDEO_18", "is_new": True},
            {"key": "video19", "title": "🎥 الاتجاه الصاعد والهابط - شرح نظري", "file_id": "PLACEHOLDER_VIDEO_19", "is_new": True},
            {"key": "video20", "title": "🎥 الاتجاه الصاعد والهابط - تطبيق عملي", "file_id": "PLACEHOLDER_VIDEO_20", "is_new": False},
            {"key": "video21", "title": "🎥 الدعم والمقاومة - شرح نظري", "file_id": "PLACEHOLDER_VIDEO_21", "is_new": False},
            {"key": "video22", "title": "🎥 الدعم والمقاومة - شرح عملي", "file_id": "PLACEHOLDER_VIDEO_22", "is_new": False},
            {"key": "video23", "title": "🎥 مؤشر RSI", "file_id": "PLACEHOLDER_VIDEO_23", "is_new": False},
            {"key": "video24", "title": "🎥 مؤشر Stochastic", "file_id": "PLACEHOLDER_VIDEO_24", "is_new": False},
            {"key": "video26", "title": "🎥 مؤشر MACD", "file_id": "PLACEHOLDER_VIDEO_26", "is_new": False},
            {"key": "video28", "title": "🎥 فيبوناتشي", "file_id": "PLACEHOLDER_VIDEO_28", "is_new": False},
            {"key": "video30", "title": "🎥 الفراغات السعرية", "file_id": "PLACEHOLDER_VIDEO_30", "is_new": False},
            {"key": "video31", "title": "🎥 النماذج السعرية الكلاسيكية - الجزء الأول", "file_id": "PLACEHOLDER_VIDEO_31", "is_new": False},
            {"key": "video32", "title": "🎥 النماذج السعرية الكلاسيكية - الجزء الثاني", "file_id": "PLACEHOLDER_VIDEO_32", "is_new": False},
            {"key": "video33", "title": "🎥 النماذج السعرية الكلاسيكية - الجزء الثالث", "file_id": "PLACEHOLDER_VIDEO_33", "is_new": False},
        ],
    },
    "idea4": {
        "title": "🕯️ الشموع اليابانية",
        "description": "في هذا القسم ستتعلم قراءة الشموع اليابانية وأهم النماذج المستخدمة في التحليل.",
        "videos": [
            {"key": "video34", "title": "🎥 مقدمة عن الشموع اليابانية", "file_id": "PLACEHOLDER_VIDEO_34", "is_new": True},
            {"key": "video35", "title": "🎥 المطرقة والمطرقة المقلوبة والرجل المشنوق", "file_id": "PLACEHOLDER_VIDEO_35", "is_new": True},
            {"key": "video36", "title": "🎥 نجمة الصباح ونجمة المساء", "file_id": "PLACEHOLDER_VIDEO_36", "is_new": False},
            {"key": "video37", "title": "🎥 شمعة الدوجي", "file_id": "PLACEHOLDER_VIDEO_37", "is_new": False},
            {"key": "video38", "title": "🎥 الشموع عالية الظلال", "file_id": "PLACEHOLDER_VIDEO_38", "is_new": False},
            {"key": "video39", "title": "🎥 الابتلاع الشرائي والبيعي", "file_id": "PLACEHOLDER_VIDEO_39", "is_new": False},
            {"key": "video40", "title": "🎥 السحابة القاتمة والخط الثاقب", "file_id": "PLACEHOLDER_VIDEO_40", "is_new": False},
            {"key": "video41", "title": "🎥 الهرامي الشرائي والبيعي", "file_id": "PLACEHOLDER_VIDEO_41", "is_new": False},
        ],
    },
    "idea5": {
        "title": "📚 نصائح للمتداولين",
        "description": "في هذا القسم ستتعلم نصائح مهمة للمتداولين وكيفية إنشاء حساب تجريبي وإدارة رأس المال.",
        "videos": [
            {"key": "video42", "title": "🎥 كيف نعمل حساب تجريبي", "file_id": "PLACEHOLDER_VIDEO_42", "is_new": True},
            {"key": "video43", "title": "🎥 نصائح لإدارة رأس المال", "file_id": "PLACEHOLDER_VIDEO_43", "is_new": True},
        ],
    },
}

TOTAL_VIDEOS = sum(len(section["videos"]) for section in VIDEO_CATALOG.values())
PAYMENT_TEXTS = {"pay_usdt":"💳 الدفع عبر USDT\n\nBEP20:\n0xDBbD77bF4aD00576F66EB8be244E278B813cA8Db\n\nTRC20:\nTW15xXADYSPytvCsoGxA9Z988h35HpJtrN","pay_syriatel":"💰 الدفع عبر سيريتل كاش\n\nالرقم:\n31623094","pay_sham":"💎 الدفع عبر شام كاش\n\nالمعرف:\n4d0c06e319a22353274375a58987f44b\n\nاسم الحساب:\nمجد غسان القيم","pay_bank":"🏦 تحويل بنكي\n\nIBAN:\nبنك البركة\n1270444","pay_cash":"💵 حوالة نقدية\n\nالاسم:\nمجد غسان القيم\nالهاتف:\n0937872522"}
FAQ_TEXT = "❓ الأسئلة الشائعة\n\n1) هل الوصول إلى الكورس دائم؟\nنعم، الوصول دائم بعد تأكيد الدفع.\n\n2) هل أستطيع مشاهدة الفيديوهات أكثر من مرة؟\nنعم.\n\n3) ماذا أفعل إذا تم رفض إشعار الدفع؟\nأرسل صورة أوضح لإشعار الدفع ثم أعد المحاولة.\n\n4) هل يمكن إعادة توجيه الفيديوهات؟\nلا، الفيديوهات محمية داخل البوت."
COURSE_OVERVIEW_TEXT = "📘 محتوى الكورس\n\n1️⃣ المصطلحات الأساسية\n2️⃣ التحليل الأساسي\n3️⃣ التحليل الفني\n4️⃣ الشموع اليابانية\n5️⃣ نصائح للمتداولين\n\n💲 سعر الكورس: 25$"
