# bot_downloader.py
# شغّله: python bot_downloader.py

import logging
import os
import tempfile
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import yt_dlp

# ────────────────────────────────────────────────
TOKEN = "8547768233:AAFqr2dIJ5OhQ5T0h9EiwpNrIc9zKBV7SAs"          # ضع توكن البوت هنا
# ────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': '%(title)s.%(ext)s',
    'noplaylist': True,               # ننزّل فيديو واحد فقط حتى لو رابط قائمة تشغيل
    'continuedl': True,
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "مرحبا! 📥\n"
        "ارسل لي رابط يوتيوب أو تيك توك (أو أي موقع مدعوم)\n"
        "وأنا بحمّل الفيديو وأرسله لك جاهز للتحميل.\n\n"
        "أمثلة:\n"
        "• https://www.youtube.com/watch?v=...\n"
        "• https://www.tiktok.com/@user/video/...\n"
        "• https://www.instagram.com/reel/...\n"
    )
    await update.message.reply_text(text)


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("أرسل رابط صحيح يبدأ بـ http أو https")
        return

    status_msg = await update.message.reply_text("جاري التحميل... ⏳ (قد يأخذ وقتاً حسب طول الفيديو)")

    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            ydl_opts['outtmpl'] = os.path.join(tmpdirname, '%(title)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            if not os.path.exists(filename):
                await status_msg.edit_text("تعذّر العثور على الملف بعد التحميل 😕")
                return

            file_size_mb = os.path.getsize(filename) / (1024 * 1024)

            if file_size_mb > 100:
                await status_msg.edit_text(
                    f"الفيديو كبير جداً ({file_size_mb:.1f} MB)\n"
                    "تليجرام يسمح للبوتات بإرسال ملفات حتى 100 ميجا فقط.\n"
                    "جرب رابط أقصر أو قسّم الفيديو."
                )
                return

            await status_msg.edit_text("جاري الإرسال... 📤")

            with open(filename, 'rb') as video_file:
                await update.message.reply_document(
                    document=video_file,
                    caption=f"تم التحميل: {info.get('title', 'فيديو')}\n{url}",
                    filename=os.path.basename(filename)
                )

            await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        logger.error(e)
        await status_msg.edit_text("تعذّر تحميل الفيديو 😔\nغالباً الرابط غير صحيح أو المحتوى مقيّد.")
    except Exception as e:
        logger.error(e, exc_info=True)
        await status_msg.edit_text("تم التحميل")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("البوت يعمل...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
