import telebot
from telebot import types
import os

# بيانات البوت والـ ID الخاص بك
API_TOKEN = '8722620250:AAGQwZOIhwczYn4LRdDheAHV4wdsiocTNck'
ADMIN_ID = 1411512309  

bot = telebot.TeleBot(API_TOKEN)
RATE_FILE = "rate.txt"

def get_stored_rate():
    if os.path.exists(RATE_FILE):
        with open(RATE_FILE, "r") as f:
            try: return float(f.read().strip())
            except: return 225.0
    return 225.0

def save_rate(new_rate):
    with open(RATE_FILE, "w") as f: f.write(str(new_rate))

user_status = {}
user_platform = {}
user_goal = {} # لتخزين هدف الإعلان (تفاعل، رسائل، إلخ)

# --- رسالة الترحيب ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 الحساب العادي بالدينار", "🔄 الحساب العكسي (بالدولار)")
    markup.add("🛡️ فحص محتوى الإعلان", "❓ الأسئلة الشائعة")
    if message.from_user.id == ADMIN_ID:
        markup.add("⚙️ إعدادات الأدمن")
    
    bot.send_message(message.chat.id, 
                     "👋 مرحباً بك في بوت خدمات السبونسور!\n\n"
                     "اختر الخدمة المطلوبة لبدء الحساب التقريبي لعمليتك:", reply_markup=markup)

# --- اختيار المنصة ---
@bot.message_handler(func=lambda message: message.text in ["📊 الحساب العادي بالدينار", "🔄 الحساب العكسي (بالدولار)"])
def select_platform(message):
    user_status[message.chat.id] = "DZD_TO_USD" if "العادي" in message.text else "USD_TO_DZD"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("فيسبوك 🔵", callback_data="facebook"),
               types.InlineKeyboardButton("إنستغرام 📸", callback_data="instagram"),
               types.InlineKeyboardButton("تيك توك 🎵", callback_data="tiktok"))
    bot.send_message(message.chat.id, "اختر المنصة المستهدفة:", reply_markup=markup)

# --- اختيار هدف الإعلان (تفاعل، رسائل، إلخ) ---
@bot.callback_query_handler(func=lambda call: call.data in ["facebook", "instagram", "tiktok"])
def select_goal(call):
    chat_id = call.message.chat.id
    user_platform[chat_id] = call.data
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    if call.data == "tiktok":
        markup.add(types.InlineKeyboardButton("زيادة المشاهدات 👁️", callback_data="goal_views"),
                   types.InlineKeyboardButton("زيادة المتابعين ➕", callback_data="goal_followers"))
    else:
        markup.add(types.InlineKeyboardButton("تفاعل (لايكات وتعليقات) 👍", callback_data="goal_engagement"),
                   types.InlineKeyboardButton("رسائل (Messenger/WhatsApp) 💬", callback_data="goal_messages"),
                   types.InlineKeyboardButton("زيادة متابعين الصفحة 👥", callback_data="goal_followers"))
    
    bot.edit_message_text("ما هو الهدف من إعلانك؟", chat_id, call.message.message_id, reply_markup=markup)

# --- طلب المبلغ بعد اختيار الهدف ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("goal_"))
def ask_amount(call):
    chat_id = call.message.chat.id
    user_goal[chat_id] = call.data
    mode = user_status.get(chat_id)
    prompt = "أدخل المبلغ بالدينار (DZD):" if mode == "DZD_TO_USD" else "أدخل قيمة الدولار ($) المطلوبة:"
    bot.send_message(chat_id, prompt)

# --- معالجة الحسابات والإحصائيات بناءً على الهدف ---
@bot.message_handler(func=lambda message: message.text.isdigit() or message.text.replace('.','',1).isdigit())
def process_calculation(message):
    chat_id = message.chat.id
    try:
        val = float(message.text)
        rate = get_stored_rate()
        mode = user_status.get(chat_id, "DZD_TO_USD")
        platform = user_platform.get(chat_id, "facebook")
        goal = user_goal.get(chat_id, "goal_engagement")

        # منطق العمولات
        if mode == "DZD_TO_USD":
            dzd = val
            if dzd < 6000: p = 600
            elif 6000 <= dzd < 10000: p = 800
            elif 10000 <= dzd < 15000: p = 1000
            else: p = 1500
            usd = (dzd - p) / rate
        else:
            usd = val
            raw_dzd = usd * rate
            if raw_dzd < 5400: p = 600
            elif 5400 <= raw_dzd < 9200: p = 800
            elif 9200 <= raw_dzd < 13500: p = 1000
            else: p = 1500
            dzd = raw_dzd + p

        # --- حساب الإحصائيات المتغيرة حسب الهدف ---
        stats_text = ""
        if goal == "goal_engagement":
            res = (usd * 200, usd * 600)
            stats_text = f"📍 التفاعل المتوقع: من {res[0]:,.0f} إلى {res[1]:,.0f} تفاعل"
        elif goal == "goal_messages":
            res = (usd * 5, usd * 15)
            stats_text = f"📍 الرسائل المتوقعة: من {res[0]:,.0f} إلى {res[1]:,.0f} رسالة"
        elif goal == "goal_followers":
            res = (usd * 50, usd * 150)
            stats_text = f"📍 المتابعين الجدد: من {res[0]:,.0f} إلى {res[1]:,.0f} متابع"
        elif goal == "goal_views":
            res = (usd * 4000, usd * 9000)
            stats_text = f"📍 المشاهدات المتوقعة: من {res[0]:,.0f} إلى {res[1]:,.0f} مشاهدة"

        final_res = (
            f"📊 **نتائج الحساب التقريبي:**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 تدفع بالدينار: {dzd:,.0f} DZD\n"
            f"💵 رصيدك في
