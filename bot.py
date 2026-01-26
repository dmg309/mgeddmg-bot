import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# =======================
# إعدادات البوت
# =======================
TOKEN = "8547768233:AAFqr2dIJ5OhQ5T0h9EiwpNrIc9zKBV7SAs"
DOWNLOAD_DIR = "downloads"
COOKIES_FILE = "cookies.txt"  # ملف cookies من متصفحك

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# =======================
# أوامر البوت
# =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل رابط الفيديو لتحميله.")

# =======================
# تحميل أي رابط
# =======================
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    msg = await update.message.reply_text(f"جارٍ تحميل الرابط:\n{url}")

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'merge_output_format': 'mp4',
        'outtmpl': f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        'cookiefile': COOKIES_FILE,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            await msg.edit_text(f"تم التحميل بنجاح:\n{os.path.basename(filename)}")
            await update.message.reply_document(document=open(filename, "rb"))
    except Exception as e:
        await msg.edit_text(f"حدث خطأ أثناء التحميل:\n{str(e)}")

# =======================
# تشغيل البوت
# =======================
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("البوت يعمل الآن...")
    app.run_polling()
