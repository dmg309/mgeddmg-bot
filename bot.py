# bot_downloader.py
import logging
import os
import tempfile
import random
import requests
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
# على Railway → استخدم Environment Variables
TOKEN = os.getenv("8546899518:AAG8DJc6HV6pffpiGBpzrUf-HawRZts3zvA")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN مطلوب في الـ Environment Variables على Railway")

# ────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# قوائم الردود (ابقِ عليها كما هي أو أضف المزيد)
WELCOME_MESSAGES = [...]   # ضع القائمة اللي عندك
LOADING_MESSAGES = [...] 
SUCCESS_MESSAGES = [...]
LARGE_FILE_MESSAGES = [
    "الفيديو كبير ({size:.1f} ميجا) 📦\nما أقدر أرسله مباشرة داخل تليجرام، جاري رفعه على سيرفر خارجي...",
    "فيديو ثقيل يا {name} ({size:.1f} MB) 💾\nبرفعه لك رابط تحميل مباشر، انتظر شوي...",
]
ERROR_AGE_MESSAGES = [...]     # كما عندك
ERROR_GEO_MESSAGES = [...]
GENERAL_ERROR_MESSAGES = [...]

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': '%(title).200s.%(ext)s',
    'noplaylist': True,
    'continuedl': True,
    'retries': 10,
    'fragment_retries': 10,
    'no_check_certificate': True,
    'geo_bypass': True,
}

def upload_to_catbox(file_path):
    try:
        url = "https://catbox.moe/user/api.php"
        with open(file_path, 'rb') as f:
            files = {'fileToUpload': f}
            data = {'reqtype': 'fileupload'}
            r = requests.post(url, files=files, data=data, timeout=900)  # 15 دقيقة timeout
        if r.status_code == 200 and "https://files.catbox.moe/" in r.text:
            return r.text.strip()
        logger.error(f"Catbox فشل: {r.text[:200]}")
        return None
    except Exception as e:
        logger.error(f"خطأ في Catbox: {e}")
        return None

# start و help_command تبقى كما هي

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("أرسل رابط يبدأ بـ http أو https من فضلك 😅")
        return

    user = update.effective_user
    name = user.first_name or "الغالي"
    loading_text = random.choice(LOADING_MESSAGES).format(name=name)
    status_msg = await update.message.reply_text(loading_text)

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
            title = info.get('title', 'فيديو بدون عنوان')

            # محاولة إرسال مباشر (حد 50MB)
            if file_size_mb <= 50:
                await status_msg.edit_text("جاري الإرسال داخل تليجرام... 📤")
                with open(filename, 'rb') as video_file:
                    await update.message.reply_document(
                        document=video_file,
                        caption=f"تم التحميل: {title}\n{url}\nالحجم: {file_size_mb:.1f} ميجا",
                        filename=os.path.basename(filename)
                    )
                await update.message.reply_text(random.choice(SUCCESS_MESSAGES).format(name=name))
            else:
                # الملف كبير → رفع خارجي
                await status_msg.edit_text(
                    random.choice(LARGE_FILE_MESSAGES).format(name=name, size=file_size_mb)
                )
                upload_url = upload_to_catbox(filename)
                if upload_url:
                    await update.message.reply_text(
                        f"هاك رابط التحميل المباشر (بدون حد حجم):\n**{upload_url}**\n\n"
                        f"العنوان: {title}\n"
                        f"الحجم: {file_size_mb:.1f} ميجا\n\n"
                        "الرابط يشتغل لفترة محدودة، حمل بسرعة! 🚀"
                    )
                else:
                    await update.message.reply_text(
                        f"يا {name}، الفيديو كبير ({file_size_mb:.1f} ميجا) وحصل خطأ في الرفع 😔\n"
                        "جرب رابط أصغر أو انتظر شوي وكرر المحاولة."
                    )

            await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        # معالجة أخطاء yt-dlp (عمر، جيو، إلخ) كما عندك سابقاً
        error_str = str(e).lower()
        if any(x in error_str for x in ["age", "sign in", "restricted", "login"]):
            msg = random.choice(ERROR_AGE_MESSAGES).format(name=name)
        elif any(x in error_str for x in ["geo", "not available", "unavailable in"]):
            msg = random.choice(ERROR_GEO_MESSAGES).format(name=name)
        else:
            msg = random.choice(GENERAL_ERROR_MESSAGES).format(name=name) + f"\n{str(e)[:100]}..."
        await status_msg.edit_text(msg)
        logger.error(e)

    except Exception as e:
        await status_msg.edit_text(f"حصل خطأ غير متوقع يا {name} 😅 جرب مرة ثانية")
        logger.error(e, exc_info=True)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    print("البوت شغال على Railway...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
