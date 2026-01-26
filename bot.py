import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

# -----------------------------
# إعدادات yt-dlp
# -----------------------------
def download_media(url, output_name):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_name,
        'noplaylist': True,
        'quiet': True,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0',
        'merge_output_format': 'mp4',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_file = ydl.prepare_filename(info)
            if not os.path.exists(final_file) or os.path.getsize(final_file) == 0:
                return None, info.get('title', output_name)
            return final_file, info.get('title', output_name)
    except Exception as e:
        print(f"Error: {e}")
        return None, None

# -----------------------------
# دوال البوت
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أرسل لي أي رابط فيديو أو صوت من YouTube، TikTok، Shorts أو أي موقع مدعوم، وسأقوم بتحميله لك."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    sender = update.message.from_user.first_name or "المستخدم"

    progress_msg = await update.message.reply_text(f"{sender}، جاري التحميل...")

    # اسم الملف سيكون باسم المرسل لتسهيل التعرف عليه
    safe_name = f"{sender}_video.%(ext)s"

    file_path, title = download_media(url, safe_name)

    if file_path:
        await progress_msg.edit_text(f"{sender}، تم تحميل الفيديو بنجاح: {title}")
        await update.message.reply_document(document=open(file_path, 'rb'))
        os.remove(file_path)  # حذف الملف بعد الإرسال
    else:
        await progress_msg.edit_text(
            f"{sender}، حدث خطأ أثناء التحميل: الرابط غير صالح أو الملف فارغ."
        )

# -----------------------------
# إعداد التطبيق وتشغيل البوت
# -----------------------------
if __name__ == "__main__":
    TOKEN = "8547768233:AAFqr2dIJ5OhQ5T0h9EiwpNrIc9zKBV7SAs"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("البوت يعمل...")
    app.run_polling()
