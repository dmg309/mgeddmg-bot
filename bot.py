import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
import yt_dlp

TOKEN = "8547768233:AAFqr2dIJ5OhQ5T0h9EiwpNrIc9zKBV7SAs"  # ضع التوكن هنا
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# اختياري: ضع مسار ملف cookies الخاص باليوتيوب إذا كان الفيديو خاصًا
COOKIES_FILE = None  # مثال: "cookies.txt"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("أرسل رابط فيديو من YouTube لتحميله!")

def download_video(url: str, filename: str) -> str:
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': filename,
        'noplaylist': True,
        'quiet': True,
        'retries': 5,
        'fragment_retries': 5,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'cookies': COOKIES_FILE,  # سيستخدم ملف الكوكيز إذا موجود
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        raise Exception("تم تحميل ملف فارغ أو الرابط غير صالح!")
    return filename

def handle_message(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    user_name = update.message.from_user.first_name
    safe_name = "".join(c if c.isalnum() else "_" for c in user_name)
    out_file = os.path.join(DOWNLOAD_DIR, f"{safe_name}.mp4")

    try:
        update.message.reply_text(f"جارٍ تحميل الفيديو باسم {safe_name}...")
        downloaded_file = download_video(url, out_file)
        with open(downloaded_file, "rb") as f:
            update.message.reply_video(f)
        update.message.reply_text("تم التحميل والإرسال بنجاح!")
    except Exception as e:
        update.message.reply_text(f"حدث خطأ أثناء التحميل:\n{e}")

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
