import os
import sys
import sqlite3
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import sys
import logging

# تغییر کدینگ خروجی پیش‌فرض به utf-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# تنظیمات لاگر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# تنظیمات لاگر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تنظیمات امنیتی
ADMIN_ID = 508332264  # جایگزین با آیدی عددی خود
TOKEN = '7255395570:AAG8FH8CJRLZycXpsxSBcQlXaDS3NhBgKCY'

# تنظیمات سرویس گوگل درایو
GOOGLE_CREDS = {
    "type": "service_account",
    "project_id": "gen-lang-client-0611653672",
    "private_key_id": "b662788681a854b20709007f60743ae50c829b28",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEugIBADANBgkqhkiG9w0BAQEFAASCBKQwggSgAgEAAoIBAQCZ0hK4BQlioZ87\nrXv05mXq914pkE4wnBIHhF/J9ZKDMDZeKSu7TVnzaqYsz9chTyUm6R6sEbqTneoj\npaj5dWOWXFtcBNw/hpyNrklMjLILzgtqtxB1ALLST3EGfFmwXJH4Yd4EoXKC3PlN\n4Bx4tlsf/7Dbvy6oo9t4BB65/1Mx9p3MoF9+HbHK+yEzmje4u5LpRxNTqXAVSRn4\no+L0eT+ACv244VEPhaNTRaj8jcpU4yHIt8txedU6jaNGQc65SG8BSPypRNGMKA/M\n9ynA+fsZ43l6Fl7I10UhyPl79UV+T+eV1eG9dzp2SBWbz6mp/lwshjpboW5Z3jS9\ntbYMmsUBAgMBAAECgf92sYOAPA1h7mp7bQLu7FpN//4eVHFWpm0YdSz1H775PDAN\nDffmMBSY9agE1txKTP1+E6TMt2F2nFlv6FoweZoUYcVIMaKX4meAwbFjQFijLfs2\nqCGAJ2nVSeJiqXxhJQ1TfIa1TAnwsP2ET3Wo2ri2QwyrLyXx5ilpaBnNrGz7alOM\nfpIT5WQIAH1oCthUaPFqT/8sLOWh5NEX3gBCjnRmyy6968RhitPmSGCgbn6en1FW\nLCCy0/m0OSpmopZmtkc0z9Bxkb8+baKEB4GBncNTUYsahZoHbhy192L+rorOrMQp\n1lYifTa7J2xGji7+62tvCqdvPf5HcVD+JtXoMAkCgYEA2EWr7ODoj1uuJlE5/GH1\n4ShXOHrEzvoi9w14PSBvegSsmNuUDhd5qwbJ1C1f7HZ/kVgf0PwQ14X0Hl0hekwz\n4iMn9huf/a6HY9EpyzmtOFzAjjeLeq3texApDeMhHUGMYCYNyLIa7PVJPRS2sYiY\nWLgYaZwdT+QESdtNZPGzmgkCgYEAthOUVxcRbeipxggvoe/mw9pqmJy7t6frnZAO\nGOSmFar/CMDfhydhEZc8BpqeE8yiY9ZkFFQY52rMVl2/hzCzjhuD3ho9t1PQ4urL\n4iCMEv/8snKtZiwLB9IhYwjkTunQH3xkCpwHWIEBPPIKLEd+o0KV+8K6esSN0enY\nsO2D8TkCgYBgqruO9HReZ38ut02wxmRtkGdz4kQHs3xfatDcmZvaMS6oYDUMG2gR\njsY1pVZjzg90+qu18ITioIgd7kihbmAeatJYyb44WINBlWMV6CDJuYODzcX1PrqQ\nMAf5ohTSC9NfwoKUuy8XzQdAWvrR3Zkixp56zgG4DNXx4Sj1vqclaQKBgH9l88V8\nPpXI1gHaeHm2gqFHko52HGLE+/ejdDm2wv8mRoy5Z64Jv8GvMDDuvuzbokR5Hk2b\nClHiSFemAP129ivY1MvzUHuWCfK8lywB2gDxXL7/vpRe/NjcDsBc2GLe9uERCG7j\n/b/PhC5ArR2OaO2TCZ6/Afwky5a1KQmjJ08BAoGAR3OFmM5C/LW7l3Tpax+3zgHw\ng/QsiP+pceM8ZM+kPeoF0Gb1sOB2rZVev3u6Q54grmlwMohuwimY9gURrAg4YO/a\n1SqJ7cPKgcSbXvU5oMLPxISbxwOlaXXJFem/16FNrVwsg+YdiVZ4GCWxGvO958Nz\n8dIRehs1QWRwxkJpcBw=\n-----END PRIVATE KEY-----\n",
    "client_email": "drive-bot@gen-lang-client-0611653672.iam.gserviceaccount.com",
    "client_id": "102250012697351781422",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/drive-bot%40gen-lang-client-0611653672.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# مسیرهای سیستمی
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIPT_DIR = os.path.join(BASE_DIR, "receipts")
DB_PATH = os.path.join(BASE_DIR, "receipts.db")

# ایجاد پوشه مورد نیاز
os.makedirs(RECEIPT_DIR, exist_ok=True)

# پیام‌های ثابت
MESSAGES = {
    'start': """سلام و درود 👋

💲 هزینه ارتقا حساب:
• 1 ماهه (30 ساعت تبدیل): 80 هزار تومان  
• 1 ماهه (50 ساعت تبدیل): 150 هزار تومان
• 3 ماهه (120 ساعت تبدیل): 400 هزار تومان

💰 شماره کارت برای پرداخت:
<code>5859831146061881</code>
به نام: ختائی

📌   پس از پرداخت، رسید پرداخت را ارسال کنید و رسید فیک ارسال نفرمایید.""",
    
    'receipt_received': "✅ رسید دریافت شد. پس از بررسی، اشتراک شما فعال خواهد شد.",
    'receipt_error': "❌ خطا در پردازش رسید. لطفاً مجدداً تلاش کنید.",
    'access_denied': "⛔️ دسترسی محدود"
}

# مدیریت دیتابیس
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            timestamp TEXT NOT NULL,
            file_path TEXT NOT NULL,
            drive_file_id TEXT,
            status TEXT DEFAULT 'pending',
            file_size INTEGER
        )
        """)
        logger.info("پایگاه داده با موفقیت راه‌اندازی شد")

# سرویس Google Drive
class DriveService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.credentials = service_account.Credentials.from_service_account_info(
            GOOGLE_CREDS,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        self.service = build('drive', 'v3', credentials=self.credentials)
        self.folder_id = self._get_or_create_folder()
        logger.info("اتصال به گوگل درایو با موفقیت انجام شد")
    
    def _get_or_create_folder(self):
        query = "mimeType='application/vnd.google-apps.folder' and name='receipts' and trashed=false"
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            includeItemsFromAllDrives=True,
            supportsAllDrives=True
        ).execute()
        
        items = results.get('files', [])
        if items:
            return items[0]['id']
        
        folder_metadata = {
            'name': 'receipts',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        logger.info(f"پوشه جدید در درایو ایجاد شد: {folder.get('id')}")
        return folder.get('id')
    
    def upload_file(self, file_path, file_name):
        file_metadata = {
            'name': file_name,
            'parents': ['1Jtir-vrFM6EpryJNWMBM8dris1QQ23Ez']
        }
        
        media = MediaFileUpload(
            file_path,
            mimetype='image/jpeg',
            resumable=True
        )
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        logger.info(f"آپلود موفق: {file_name} (ID: {file.get('id')})")
        return file.get('id')

# دستورات ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        MESSAGES['start'],
        parse_mode='HTML'
    )
    logger.info(f"کاربر {update.effective_user.id} دستور start را اجرا کرد")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    photo = update.message.photo[-1]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    filename = f"receipt_{user.id}_{user.username or 'no_username'}_{user.first_name or ''}_{user.last_name or ''}_{timestamp}.jpg"
    filename = filename.replace(" ", "_")
    filepath = os.path.join(RECEIPT_DIR, filename)
    
    logger.info(f"شروع پردازش رسید از کاربر {user.id} ({user.username})")

    try:
        file = await photo.get_file()
        logger.info(f"فایل از تلگرام دریافت شد (ID: {file.file_id})")

        await file.download_to_drive(custom_path=filepath)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError("فایل پس از دانلود وجود ندارد")
        
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            raise ValueError("فایل دانلود شده خالی است")
        logger.info(f"فایل با حجم {file_size} بایت ذخیره شد")

        drive = DriveService()
        drive_id = drive.upload_file(filepath, filename)
        
        if not drive_id:
            raise ConnectionError("آپلود به گوگل درایو ناموفق بود")

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """INSERT INTO receipts 
                (user_id, username, first_name, last_name, timestamp, file_path, drive_file_id, file_size) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user.id, 
                    user.username, 
                    user.first_name, 
                    user.last_name,
                    timestamp, 
                    filepath, 
                    drive_id, 
                    file_size
                )
            )
        
        await update.message.reply_text(MESSAGES['receipt_received'])
        logger.info(f"رسید کاربر {user.id} با موفقیت پردازش شد")

    except Exception as e:
        logger.error(f"خطا در پردازش رسید: {type(e).__name__}: {e}", exc_info=True)
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                logger.info(f"فایل موقت حذف شد: {filepath}")
            except Exception as del_err:
                logger.error(f"خطا در حذف فایل موقت: {del_err}")
        
        await update.message.reply_text(MESSAGES['receipt_error'])

async def show_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(MESSAGES['access_denied'])
        return
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, first_name, last_name, timestamp, drive_file_id, file_size 
                FROM receipts 
                ORDER BY id DESC 
                LIMIT 10
            """)
            records = cursor.fetchall()
        
        if not records:
            await update.message.reply_text("📭 هیچ رسیدی ثبت نشده")
            return
        
        response = ["📋 آخرین 10 رسید:"]
        for idx, (user_id, username, first_name, last_name, timestamp, drive_id, file_size) in enumerate(records, 1):
            drive_link = f"https://drive.google.com/file/d/{drive_id}" if drive_id else "آپلود نشد"
            response.append(
                f"{idx}. 👤 {user_id} | @{username or 'بدون یوزرنیم'} | {first_name or ''} {last_name or ''}\n"
                f"   🕒 {timestamp}\n"
                f"   📦 {file_size // 1024} KB\n"
                f"   🔗 {drive_link}"
            )
        
        await update.message.reply_text("\n".join(response))
        logger.info(f"ادمین {update.effective_user.id} لیست رسیدها را مشاهده کرد")
        
    except Exception as e:
        logger.error(f"خطا در نمایش دیتابیس: {e}")
        await update.message.reply_text("⚠️ خطا در دریافت داده‌ها")

# اجرای ربات
def main():
    logger.info("🔵 شروع راه‌اندازی ربات...")
    
    init_db()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("db", show_db))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    logger.info("🟢 ربات فعال و آماده دریافت پیام...")
    app.run_polling()

if __name__ == "__main__":
    main()
