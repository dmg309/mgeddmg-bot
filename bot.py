import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import yt_dlp

TOKEN = "8547768233:AAFqr2dIJ5OhQ5T0h9EiwpNrIc9zKBV7SAs"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط فيديو من YouTube لتحميله!")

def download_video(url: str, filename: str) -> str:
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': filename,  # يحفظ مباشرة في نفس المسار
        'noplaylist': True,
        'quiet': True,
        'retries': 5,
        'fragment_retries': 5,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        raise Exception("تم تحميل ملف فارغ أو الرابط غير صالح!")
    return filename

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_name = update.message.from_user.first_name
    safe_name = "".join(c if c.isalnum() else "_" for c in user_name)
    out_file = f"{safe_name}.mp4"  # حفظ الفيديو مباشرة في نفس المسار باسم المستخدم

    try:
        await update.message.reply_text(f"جارٍ تحميل الفيديو باسم {safe_name}...")
        download_video(url, out_file)
        with open(out_file, "rb") as f:
            await update.message.reply_video(f)
        await update.message.reply_text("تم التحميل والإرسال بنجاح!")
        os.remove(out_file)  # حذف الملف بعد الإرسال لتجنب تراكم الملفات
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء التحميل:\n{e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
