import telebot
from telebot import types
import os

# بيانات البوت الخاصة بك التي قدمتها
API_TOKEN = '8722620250:AAGQwZOIhwczYn4LRdDheAHV4wdsiocTNck'
ADMIN_ID = 1411512309  

bot = telebot.TeleBot(API_TOKEN)
RATE_FILE = "rate.txt"

# --- إدارة سعر الصرف (يُحفظ في ملف ليبقى ثابتاً حتى لو توقف البوت) ---
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
FORBIDDEN_KEYWORDS = ["سلاح", "دواء", "تخسيس", "ربح سريع", "قمار", "رهان", "مخدرات"]

# --- رسالة الترحيب والقائمة الرئيسية ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    current_rate = get_stored_rate()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 الحساب العادي بالدينار", "🔄 المبلغ الذي تدفعه مقابل قيمة الدولار")
    markup.add("🛡️ فحص محتوى الإعلان", "❓ الأسئلة الشائعة")
    if message.from_user.id == ADMIN_ID:
        markup.add("⚙️ إعدادات الأدمن")
    
    bot.send_message(message.chat.id, 
                     f"👋 مرحباً بك في بوت خدمات السبونسور!\n"
                     f"💵 سعر الصرف الحالي: {current_rate} دج/$\n\n"
                     f"اختر الخدمة المطلوبة:", reply_markup=markup)

# --- قسم الأسئلة الشائعة ---
@bot.message_handler(func=lambda message: message.text == "❓ الأسئلة الشائعة")
def faq_section(message):
    faq_text = (
        "💡 **معلومات تهمك:**\n\n"
        "📍 **كيف أبدأ؟** اختر نوع الحساب ثم المنصة وأدخل المبلغ.\n"
        "📍 **طرق الدفع؟** بريدي موب (Baridimob) أو CCP.\n"
        "📍 **وقت التفعيل؟** مراجعة الإعلانات تأخذ عادة من 2 إلى 24 ساعة.\n"
        "📍 **دقة الإحصائيات؟** الأرقام تقريبية وتعتمد على جودة المحتوى المستهدف."
    )
    bot.reply_to(message, faq_text, parse_mode='Markdown')

# --- نظام مراقبة المحتوى ---
@bot.message_handler(func=lambda message: message.text == "🛡️ فحص محتوى الإعلان")
def check_policy(message):
    user_status[message.chat.id] = "CHECKING_TEXT"
    bot.send_message(message.chat.id, "📥 أرسل نص الإعلان أو الرابط لفحصه:")

# --- اختيار المنصة (فيسبوك، إنستغرام، تيك توك) ---
@bot.message_handler(func=lambda message: message.text in ["📊 الحساب العادي بالدينار", "🔄 المبلغ الذي تدفعه مقابل قيمة الدولار"])
def select_platform(message):
    user_status[message.chat.id] = "DZD_TO_USD" if "العادي" in message.text else "USD_TO_DZD"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("فيسبوك 🔵", callback_data="facebook"),
               types.InlineKeyboardButton("إنستغرام 📸", callback_data="instagram"),
               types.InlineKeyboardButton("تيك توك 🎵", callback_data="tiktok"))
    bot.send_message(message.chat.id, "اختر المنصة المستهدفة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    if call.data == "admin_settings":
        msg = bot.send_message(chat_id, "📥 أرسل سعر الصرف الجديد (أرقام فقط):")
        bot.register_next_step_handler(msg, update_rate_process)
        return

    user_platform[chat_id] = call.data
    mode = user_status.get(chat_id)
    prompt = "أدخل المبلغ بالدينار (DZD):" if mode == "DZD_TO_USD" else "أدخل قيمة الدولار ($) المطلوبة:"
    bot.send_message(chat_id, f"✅ تم اختيار {call.data.upper()}\n{prompt}")

def update_rate_process(message):
    try:
        new_rate = float(message.text)
        save_rate(new_rate)
        bot.reply_to(message, f"✅ تم تحديث السعر بنجاح لـ: {new_rate} دج")
    except: bot.reply_to(message, "⚠️ خطأ! يرجى إرسال رقم صحيح.")

# --- المعالجة والتقارير التلقائية للأدمن ---
@bot.message_handler(func=lambda message: True)
def process_all(message):
    chat_id = message.chat.id
    text = message.text

    # معالجة فحص المراقبة
    if user_status.get(chat_id) == "CHECKING_TEXT":
        found = [w for w in FORBIDDEN_KEYWORDS if w in text.lower()]
        if found:
            bot.reply_to(message, f"⚠️ تحذير! قد يتم رفض إعلانك لوجود كلمات مشبوهة: ({', '.join(found)})")
        else:
            bot.reply_to(message, "✅ النص يبدو آمناً للاستخدام في الإعلانات.")
        user_status[chat_id] = None
        return

    # لوحة إعدادات الأدمن
    if text == "⚙️ إعدادات الأدمن" and chat_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("تعديل سعر الصرف 💹", callback_data="admin_settings"))
        bot.send_message(chat_id, "لوحة التحكم الخاصة بك:", reply_markup=markup)
        return

    # منطق الحساب المالي
    try:
        val = float(text)
        rate = get_stored_rate()
        mode = user_status.get(chat_id, "DZD_TO_USD")
        platform = user_platform.get(chat_id, "facebook")

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

        # إحصائيات تقريبية للمنصات
        if platform == "facebook": r = (usd*1600, usd*3400); l = "الوصول"
        elif platform == "instagram": r = (usd*1100, usd*2500); l = "الظهور"
        else: r = (usd*3800, usd*8500); l = "المشاهدات"

        # إرسال النتيجة للزبون
        res = (
            f"📊 **نتيجة الحساب:**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 تدفع بالدينار: {dzd:,.0f} DZD\n"
            f"💵 تستلم بالدولار: **{usd:.2f} USD**\n"
            f"✂️ عمولة الخدمة: {p} دج\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📈 إحصائيات {platform.upper()} المتوقعة:\n"
            f"📍 {l}: من {r[0]:,.0f} إلى {r[1]:,.0f}\n"
        )
        bot.send_message(chat_id, res, parse_mode='Markdown')

        # إرسال تقرير استعلام صامت للأدمن (أنت)
        admin_report = (
            f"👤 **شخص استعلم الآن:**\n"
            f"• الاسم: {message.from_user.first_name}\n"
            f"• اليوزر: @{message.from_user.username or 'بدون معرف'}\n"
            f"• المبلغ: {dzd:,.0f} DZD\n"
            f"• المنصة: {platform.upper()}"
        )
        bot.send_message(ADMIN_ID, admin_report)

    except ValueError:
        pass

bot.polling(none_stop=True)
      
