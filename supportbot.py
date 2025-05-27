import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Google Drive API
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# مسیر ایمن فایل credentials.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "credentials.json")

# تنظیمات گوگل درایو
SCOPES = ['https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

# تابع یافتن یا ساختن پوشه
def get_or_create_receipts_folder():
    query = "mimeType='application/vnd.google-apps.folder' and name='receipts' and trashed=false"
    results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    folder_metadata = {
        'name': 'receipts',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    return folder.get('id')

FOLDER_ID = get_or_create_receipts_folder()

def upload_to_drive(file_path, file_name):
    file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}
    media = MediaFileUpload(file_path, resumable=True)
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    print(f"✅ آپلود شد در گوگل درایو. File ID: {uploaded_file.get('id')}")
    return uploaded_file.get('id')

# مشخصات ادمین
ADMIN_ID = 508332264

# مسیر ذخیره‌سازی
RECEIPT_DIR = os.path.join(BASE_DIR, "receipts")
os.makedirs(RECEIPT_DIR, exist_ok=True)

# دیتابیس
DB_PATH = os.path.join(BASE_DIR, "receipts.db")
conn = sqlite3.connect(DB_PATH)
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
conn.close()

# پیام‌ها
message_1 = """سلام و درود

💲هزینه ارتقا برای 1 ماه:

تبدیل 30 ساعت فایل صوتی یا تصویری 80 هزار تومان  
تبدیل 50 ساعت فایل صوتی یا تصویری 150 هزار تومان

3 ماهه: مجموعا 1200 ساعت تبدیل 400 تومن

هر 15 ساعت خلاصه اضافه 75 هزار تومان است

تمام پلن‌ها دارای:
⭐️ 5 ساعت خلاصه‌نویسی هدیه

برای شارژ فقط به شماره کارت‌های زیر مبلغ موردنظر را واریز کرده و عکس رسید را ارسال کنید، آنلاین بشم شارژ انجام میشه 🙏

‼️ لطفاً ابتدا از بات به‌صورت رایگان استفاده کرده و در صورت رضایت، اشتراک تهیه کنید.
"""

message_2 = """شماره کارت‌ها:

5859831146061881

ختائی

بزنید روی شماره کارت‌ها تا کپی بشن. بهتره اولی رو امتحان کنید، اگر تراکنشش پر بود، از بقیه استفاده کنید.

❌ لطفاً رسید فیک، تکراری یا قدیمی نفرستید. تمام رسیدها دقیق بررسی می‌شوند.
"""

# دستور start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(message_1)
    await update.message.reply_text(message_2)

# دریافت رسید عکس
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO receipts (user_id, username, timestamp, file_path) VALUES (?, ?, ?, ?)",
        (user_id, username, timestamp, filepath)
    )
    conn.commit()
    conn.close()

    # آپلود در گوگل درایو
    upload_to_drive(filepath, filename)

    # ارسال به ادمین
    caption = f"🆔 User ID: {user_id}\n"
    if username:
        caption += f"👤 Username: @{username}\n"
    caption += f"🕒 Time: {timestamp}"

    with open(filepath, "rb") as f:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=f, caption=caption)

    await update.message.reply_text("✅ رسید شما دریافت شد و پس از بررسی، توکن شما فعال می‌شود.")

# دریافت chat_id برای تست
async def log_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    print(f"📡 Chat ID: {chat.id} | Type: {chat.type}")

# نمایش دیتابیس (فقط ادمین)
async def show_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ شما به این دستور دسترسی ندارید.")
        return

    conn = sqlite3.connect(DB_PATH)
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

# اجرای ربات
def main():
    TOKEN = "7255395570:AAG8FH8CJRLZycXpsxSBcQlXaDS3NhBgKCY"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("db", show_db))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.ALL, log_chat_id))

    print("🤖 ربات فعال شد.")
    app.run_polling()

if __name__ == "__main__":
    main()
