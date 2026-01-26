# bot_with_large_file_links.py

import logging
import os
import tempfile
import subprocess

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.request import HTTPXRequest

import yt_dlp

TOKEN = "8546899518:AAFByazYsuYidgsVtBcYu4LpnGBAJBmztF0"
MAX_MB = 50

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BASE_YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "merge_output_format": "mp4",
    "http_headers": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    },
}

# ─────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "صديقي"
    await update.message.reply_text(
        f"أهلاً وسهلاً {user_name}!\n"
        "أرسل رابط فيديو من YouTube / TikTok / Instagram\n\n"
        "ثم اختر:\n"
        "🎬 جودة عالية (1080p)\n"
        "🎥 جودة متوسطة (720p)\n"
        "🎵 صوت فقط MP3"
    )

# ─────────────────────────
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("أرسل رابط صحيح يبدأ بـ http أو https")
        return

    context.user_data["url"] = url
    keyboard = [
        [InlineKeyboardButton("🎬 جودة عالية (1080p)", callback_data="video_high")],
        [InlineKeyboardButton("🎥 جودة متوسطة (720p)", callback_data="video_mid")],
        [InlineKeyboardButton("🎵 صوت فقط MP3", callback_data="audio")],
    ]
    await update.message.reply_text("اختر صيغة التحميل:", reply_markup=InlineKeyboardMarkup(keyboard))

# ─────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get("url")
    if not url:
        await query.edit_message_text("انتهت الجلسة، أرسل الرابط من جديد.")
        return

    await query.edit_message_text("⏳ جاري التحميل...")

    try:
        with tempfile.TemporaryDirectory() as tmp:
            ydl_opts = BASE_YDL_OPTS.copy()
            ydl_opts["outtmpl"] = os.path.join(tmp, "%(title)s.%(ext)s")

            mode = query.data

            if mode == "video_high":
                ydl_opts["format"] = (
                    "bestvideo[height<=1080][ext=mp4][vcodec!=vp9]+"
                    "bestaudio[ext=m4a]/best[ext=mp4]"
                )
            elif mode == "video_mid":
                ydl_opts["format"] = (
                    "bestvideo[height<=720][ext=mp4][vcodec!=vp9]+"
                    "bestaudio[ext=m4a]/best[ext=mp4]"
                )
            elif mode == "audio":
                ydl_opts["format"] = "bestaudio"
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            if mode == "audio":
                filename = filename.rsplit(".", 1)[0] + ".mp3"

            size_mb = os.path.getsize(filename) / (1024 * 1024)

            # ضغط الفيديو إذا تجاوز الحد
            if size_mb > MAX_MB and mode != "audio":
                compressed = os.path.join(tmp, "compressed.mp4")
                subprocess.run(
                    ["ffmpeg", "-y", "-i", filename, "-vcodec", "libx264",
                     "-crf", "28", "-preset", "veryfast", "-acodec", "aac", compressed],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                filename = compressed
                size_mb = os.path.getsize(filename) / (1024 * 1024)

            # إذا تجاوز الحد بعد الضغط، نرفع الملف ونرسل رابط مباشر
            if size_mb > MAX_MB:
                # نرسل الملف للـ Saved Messages الخاص بالبوت نفسه
                bot_message = await context.bot.send_document(
                    chat_id=update.effective_user.id,
                    document=open(filename, "rb"),
                    filename=os.path.basename(filename),
                )
                file_id = bot_message.document.file_id
                download_link = f"https://t.me/c/{bot_message.chat.id}/{bot_message.message_id}"
                await query.edit_message_text(
                    f"✅ تم رفع الملف بنجاح!\nحجم الملف: {size_mb:.1f}MB\n"
                    f"يمكنك تحميله مباشرة من الرابط:\n{download_link}"
                )
                return

            # رفع الملفات الصغيرة مباشرة
            with open(filename, "rb") as f:
                await query.message.reply_document(
                    document=f,
                    filename=os.path.basename(filename),
                    caption=f"✅ تم التحميل\n{info.get('title','')}",
                )
            await query.message.delete()

    except Exception as e:
        logger.error("Error downloading: %s", e, exc_info=True)
        await query.edit_message_text(f"❌ حدث خطأ أثناء التحميل:\n{e}")

# ─────────────────────────
def main():
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=180,
        write_timeout=180,
        connect_timeout=30,
    )
    app = Application.builder() \
        .token(TOKEN) \
        .request(request) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
