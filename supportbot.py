import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# مشخصات ادمین
ADMIN_ID = 508332264

# مسیر ذخیره‌سازی عکس‌ها
RECEIPT_DIR = "receipts"
os.makedirs(RECEIPT_DIR, exist_ok=True)

# ساخت دیتابیس
conn = sqlite3.connect("receipts.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    timestamp TEXT,
    file_path TEXT
)
""")
conn.commit()

# پیام‌های ثابت
message_1 = """سلام و درود

💲هزینه ارتقا برای 1 ماه:

تبدیل 20 ساعت فایل صوتی یا تصویری 80 هزار تومان  
تبدیل 40 ساعت فایل صوتی یا تصویری 150 هزار تومان

3 ماهه: مجموعا 100 ساعت تبدیل 400 تومن

هر 10 ساعت خلاصه اضافه 75 هزار تومان است

تمام پلن‌ها دارای:
⭐️ 5 ساعت خلاصه‌نویسی هدیه

برای شارژ فقط به شماره کارت‌های زیر مبلغ موردنظر را واریز کرده و عکس رسید را ارسال کنید، آنلاین بشم شارژ انجام میشه 🙏

‼️ لطفاً ابتدا از بات به‌صورت رایگان استفاده کرده و در صورت رضایت، اشتراک تهیه کنید.
"""

message_2 = """شماره کارت‌ها:

6219861809407074  
6219861064486367  
6037998288276487  

بزنید روی شماره کارت‌ها تا کپی بشن. بهتره اولی رو امتحان کنید، اگر تراکنشش پر بود، از بقیه استفاده کنید.

❌ لطفاً رسید فیک، تکراری یا قدیمی نفرستید. تمام رسیدها دقیق بررسی می‌شوند.
"""

# فرمان /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(message_1)
    await update.message.reply_text(message_2)

# دریافت عکس رسید
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    username = user.username
    photo = update.message.photo[-1]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    filename = f"{user_id}_{timestamp}.jpg"
    filepath = os.path.join(RECEIPT_DIR, filename)

    file = await photo.get_file()
    await file.download_to_drive(filepath)

    # ذخیره در دیتابیس
    conn = sqlite3.connect("receipts.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO receipts (user_id, username, timestamp, file_path) VALUES (?, ?, ?, ?)",
        (user_id, username, timestamp, filepath)
    )
    conn.commit()
    conn.close()

    # ارسال برای ادمین (می‌تونی اینجا chat_id کانال رو جایگزین کنی بعداً)
    caption = f"🆔 User ID: {user_id}\n"
    if username:
        caption += f"👤 Username: @{username}\n"
    caption += f"🕒 Time: {timestamp}"

    with open(filepath, "rb") as f:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=f, caption=caption)

    # پیام به کاربر
    await update.message.reply_text("✅ رسید شما دریافت شد و پس از بررسی، توکن شما فعال می‌شود.")

# گرفتن chat_id هرجا پیامی بیاد (مثلاً کانال)
async def log_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    print(f"📡 Chat ID: {chat.id} | Type: {chat.type}")

# دستور نمایش دیتابیس فقط برای ادمین
async def show_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ شما به این دستور دسترسی ندارید.")
        return

    conn = sqlite3.connect("receipts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, timestamp FROM receipts ORDER BY id DESC LIMIT 10")
    records = cursor.fetchall()
    conn.close()

    if not records:
        await update.message.reply_text("📂 هنوز رسیدی ثبت نشده.")
        return

    message = "📊 آخرین رسیدهای ثبت‌شده:\n\n"
    for user_id, username, timestamp in records:
        if username:
            message += f"🆔 {user_id} | @{username} | 🕒 {timestamp}\n"
        else:
            message += f"🆔 {user_id} | بدون یوزرنیم | 🕒 {timestamp}\n"

    await update.message.reply_text(message)

# راه‌اندازی ربات
def main():
    TOKEN = "توکن واقعی‌ات اینجا"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("db", show_db))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.ALL, log_chat_id))  # هندلر برای log آیدی کانال و غیره

    print("🤖 ربات فعال شد.")
    app.run_polling()

if __name__ == "__main__":
    main()
