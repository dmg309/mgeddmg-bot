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
TOKEN = "8546899518:AAG8DJc6HV6pffpiGBpzrUf-HawRZts3zvA"          # ضع توكن البوت هنا
# ────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # أفضل جودة mp4
    'outtmpl': '%(title).200s.%(ext)s',  # قص الاسم عشان ما يسبب مشاكل في تليجرام
    'noplaylist': True,                  # فيديو واحد فقط
    'continuedl': True,
    'retries': 10,                       # محاولات إعادة أكثر
    'fragment_retries': 10,
    'no_check_certificate': True,        # تجاهل بعض مشاكل SSL
    'geo_bypass': True,                  # محاولة تجاوز الحجب الجغرافي
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "مرحبا! 📥\n"
        "أرسل أي رابط فيديو من أي موقع تواصل أو منصة، وأحمله لك مباشرة.\n\n"
        "يدعم تقريباً كل شيء:\n"
        "• يوتيوب + Shorts\n"
        "• تيك توك\n"
        "• إنستغرام (Reels, Posts)\n"
        "• تويتر/X\n"
        "• فيسبوك\n"
        "• ريديت، فييمو، بنترست، VK، وآلاف المواقع الأخرى 🚀\n\n"
        "فقط أرسل الرابط!"
    )
    await update.message.reply_text(text)


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("أرسل رابط صحيح يبدأ بـ http أو https من فضلك 😅")
        return

    status_msg = await update.message.reply_text("جاري التحميل... ⏳ (قد يأخذ وقتاً حسب الرابط والفيديو)")

    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            ydl_opts['outtmpl'] = os.path.join(tmpdirname, '%(title).200s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            if not os.path.exists(filename):
                await status_msg.edit_text("تعذّر العثور على الملف بعد التحميل 😕")
                return

            file_size_mb = os.path.getsize(filename) / (1024 * 1024)

            if file_size_mb > 50:
                await status_msg.edit_text(
                    f"الفيديو كبير جداً ({file_size_mb:.1f} ميجا)\n"
                    "تليجرام يحدد 50 ميجا للبوتات العادية.\n"
                    "جرب رابط أقصر أو جودة أقل إن أمكن."
                )
                return

            await status_msg.edit_text("جاري الإرسال... 📤")

            with open(filename, 'rb') as video_file:
                await update.message.reply_document(
                    document=video_file,
                    caption=f"تم التحميل: {info.get('title', 'فيديو')}\nالمصدر: {url}",
                    filename=os.path.basename(filename)
                )

            await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        error_str = str(e).lower()
        if any(word in error_str for word in ["age", "restricted", "login", "sign in"]):
            await status_msg.edit_text("الفيديو مقيد بالعمر أو يحتاج تسجيل دخول 😕")
        elif any(word in error_str for word in ["geo", "unavailable", "region"]):
            await status_msg.edit_text("الفيديو غير متاح في منطقتك 🌍 (جرب VPN)")
        else:
            await status_msg.edit_text("تعذّر التحميل 😔\nالرابط قد يكون خاطئ أو المحتوى محمي.")
        logger.error(e)

    except Exception as e:
        logger.error(e, exc_info=True)
        await status_msg.edit_text("حصل خطأ غير متوقع 😅\nجرب رابط آخر أو انتظر شوي.")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("البوت يعمل...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
