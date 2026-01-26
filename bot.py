import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import yt_dlp

# ===== إعداد المجلد لحفظ الفيديوهات =====
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===== خيارات yt_dlp مع تجاوز أخطاء TikTok 503 =====
ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'noplaylist': True,
    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    'quiet': True,
    'ignoreerrors': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.tiktok.com/',
    },
    'retries': 5,
    'fragment_retries': 5,
    'continuedl': True,
}

# ===== دالة تحميل الفيديو =====
def download_video(url: str):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            return None
        filename = ydl.prepare_filename(info)
        return filename

# ===== استقبال الفيديوهات =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    sender_name = update.message.from_user.first_name

    try:
        await update.message.reply_text(f"جارٍ تحميل الفيديو، {sender_name}...")
        file_path = download_video(url)

        if file_path and os.path.exists(file_path):
            await update.message.reply_video(video=open(file_path, "rb"), caption=f"تم التحميل بنجاح، {sender_name}!")
        else:
            await update.message.reply_text(f"عذرًا، لم أتمكن من تحميل الفيديو، {sender_name}. ربما الرابط غير مدعوم.")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء التحميل، {sender_name}.\n{str(e)}")

# ===== تشغيل البوت =====
def main():
    TOKEN = "8547768233:AAFqr2dIJ5OhQ5T0h9EiwpNrIc9zKBV7SAs"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
