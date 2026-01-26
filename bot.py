import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = "8547768233:AAFqr2dIJ5OhQ5T0h9EiwpNrIc9zKBV7SAs"  # ضع توكن البوت هنا

# مجلد مؤقت لتحميل الفيديوهات
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أرسل لي رابط الفيديو وسأقوم بتحميله لك.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_name = update.message.from_user.first_name

    await update.message.reply_text(f"جارٍ تحميل الفيديو باسم {user_name}...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            await update.message.reply_text(f"تم تحميل الفيديو: {info.get('title', 'video')}")
            await context.bot.send_document(chat_id=update.message.chat_id, document=open(file_path, 'rb'))
        else:
            await update.message.reply_text("حدث خطأ: تم تحميل ملف فارغ أو الرابط غير صالح!")

    except yt_dlp.utils.DownloadError as e:
        await update.message.reply_text(f"حدث خطأ أثناء التحميل:\n{str(e)}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
