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

user_data = {} # لتخزين كل معطيات المستخدم (المبلغ، الأيام، المنصة، الهدف)

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
    user_data[message.chat.id] = {'mode': "DZD_TO_USD" if "العادي" in message.text else "USD_TO_DZD"}
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("فيسبوك 🔵", callback_data="facebook"),
               types.InlineKeyboardButton("إنستغرام 📸", callback_data="instagram"),
               types.InlineKeyboardButton("تيك توك 🎵", callback_data="tiktok"))
    bot.send_message(message.chat.id, "اختر المنصة المستهدفة:", reply_markup=markup)

# --- اختيار هدف الإعلان ---
@bot.callback_query_handler(func=lambda call: call.data in ["facebook", "instagram", "tiktok"])
def select_goal(call):
    chat_id = call.message.chat.id
    user_data[chat_id]['platform'] = call.data
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    if call.data == "tiktok":
        markup.add(types.InlineKeyboardButton("زيادة المشاهدات 👁️", callback_data="goal_views"),
                   types.InlineKeyboardButton("زيادة المتابعين ➕", callback_data="goal_followers"))
    else:
        markup.add(types.InlineKeyboardButton("تفاعل 👍", callback_data="goal_engagement"),
                   types.InlineKeyboardButton("رسائل 💬", callback_data="goal_messages"),
                   types.InlineKeyboardButton("متابعين 👥", callback_data="goal_followers"))
    
    bot.edit_message_text("ما هو الهدف من إعلانك؟", chat_id, call.message.message_id, reply_markup=markup)

# --- طلب المبلغ ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("goal_"))
def ask_amount(call):
    chat_id = call.message.chat.id
    user_data[chat_id]['goal'] = call.data
    mode = user_data[chat_id]['mode']
    prompt = "💰 أدخل المبلغ بالدينار (DZD):" if mode == "DZD_TO_USD" else "💰 أدخل قيمة الدولار ($) المطلوبة:"
    msg = bot.send_message(chat_id, prompt)
    bot.register_next_step_handler(msg, ask_days)

# --- طلب عدد الأيام ---
def ask_days(message):
    chat_id = message.chat.id
    try:
        user_data[chat_id]['amount'] = float(message.text)
        msg = bot.send_message(chat_id, "📅 كم يوماً تريد أن تستمر الحملة؟ (أدخل رقماً):")
        bot.register_next_step_handler(msg, process_final_calculation)
    except:
        bot.reply_to(message, "⚠️ يرجى إدخال مبلغ صحيح.")

# --- الحساب النهائي ---
def process_final_calculation(message):
    chat_id = message.chat.id
    try:
        days = int(message.text)
        if days < 1: days = 1
        
        data = user_data[chat_id]
        val = data['amount']
        rate = get_stored_rate()
        mode = data['mode']
        platform = data['platform']
        goal = data['goal']

        # حساب العمولات والدولار
        if mode == "DZD_TO_USD":
            dzd = val
            if dzd < 6000: p = 600
            elif dzd < 10000: p = 800
            elif dzd < 15000: p = 1000
            else: p = 1500
            usd = (dzd - p) / rate
        else:
            usd = val
            raw_dzd = usd * rate
            if raw_dzd < 5400: p = 600
            elif raw_dzd < 9200: p = 800
            elif raw_dzd < 13500: p = 1000
            else: p = 1500
            dzd = raw_dzd + p

        usd_per_day = usd / days

        # تقدير الإحصائيات (معدلة حسب الهدف)
        if goal == "goal_engagement":
            res = (usd * 200, usd * 600); label = "تفاعل"
        elif goal == "goal_messages":
            res = (usd * 4, usd * 12); label = "رسالة"
        elif goal == "goal_followers":
            res = (usd * 45, usd * 130); label = "متابع"
        else: # مشاهدات
            res = (usd * 3500, usd * 8500); label = "مشاهدة"

        final_res = (
            f"📊 **تفاصيل حملتك الإعلانية:**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 التكلفة الإجمالية: {dzd:,.0f} DZD\n"
            f"💵 رصيد الإعلان: **{usd:.2f} USD**\n"
            f"📅 مدة الحملة: {days} أيام\n"
            f"💸 الميزانية اليومية: {usd_per_day:.2f} $/يوم\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📈 التوقعات الإجمالية ({platform.upper()}):\n"
            f"📍 {label}: من {res[0]:,.0f} إلى {res[1]:,.0f}\n"
            f"📍 يومياً: ~ {(res[0]/days):,.0f} {label}\n\n"
            f"⚠️ ملاحظة: النتائج تعتمد على محتوى إعلانك."
        )
        bot.send_message(chat_id, final_res, parse_mode='Markdown')
        bot.send_message(ADMIN_ID, f"👤 استعلام جديد من محلك:\nالمبلغ: {dzd} DZD\nالأيام: {days}\nالسعر الحالي: {rate}")

    except:
        bot.reply_to(message, "⚠️ يرجى إدخال عدد أيام صحيح (رقم).")

# --- لوحة الأدمن ---
@bot.message_handler(func=lambda message: message.text == "⚙️ إعدادات الأدمن" and message.chat.id == ADMIN_ID)
def admin_panel(message):
    curr = get_stored_rate()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("تعديل سعر الصرف", callback_data="admin_settings"))
    bot.send_message(message.chat.id, f"لوحة التحكم\nالسعر الحالي: {curr} دج", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_settings")
def admin_rate_change(call):
    bot.send_message(call.message.chat.id, "📥 أرسل سعر الصرف الجديد:")
    bot.register_next_step_handler(call.message, update_rate)

def update_rate(message):
    try:
        new_rate = float(message.text)
        save_rate(new_rate)
        bot.reply_to(message, f"✅ تم تحديث السعر لـ {new_rate} دج")
    except: bot.reply_to(message, "⚠️ خطأ في الرقم.")

bot.polling(none_stop=True)
