import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp.utils import DownloadError, UnsupportedError

# مجلد تحميل الفيديوهات
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# إعدادات yt-dlp
def get_ydl_opts(user):
    return {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'%(title)s-{user}.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }
    }

# تحقق من الروابط المدعومة
def is_supported_url(url: str) -> bool:
    supported_domains = ['youtube.com', 'youtu.be', 'tiktok.com', 'vimeo.com']
    return any(domain in url for domain in supported_domains)

# رسالة /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أرسل رابط فيديو من YouTube أو TikTok أو Vimeo لتحميله.\n"
        "ملاحظة: روابط الصور أو الخاصة على TikTok غير مدعومة."
    )

# معالجة الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user = update.message.from_user.username or update.message.from_user.first_name

    if not is_supported_url(url):
        await update.message.reply_text(
            "❌ هذا الرابط غير مدعوم.\n"
            "استخدم روابط فيديو من YouTube أو TikTok أو Vimeo."
        )
        return

    await update.message.reply_text("⏳ جاري تحميل الفيديو...")

    try:
        ydl_opts = get_ydl_opts(user)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        await update.message.reply_text(f"✅ تم تحميل الفيديو بنجاح:\n{filename}")

    except UnsupportedError:
        await update.message.reply_text(
            "❌ الرابط غير مدعوم للتحميل. "
            "قد يكون رابط صورة أو فيديو خاص على TikTok."
        )
    except DownloadError as e:
        msg = str(e)
        if "HTTP Error 503" in msg:
            reason = "الخادم غير متاح مؤقتًا (HTTP 503). حاول لاحقًا."
        elif "Private" in msg or "Login" in msg:
            reason = "الفيديو خاص أو يتطلب تسجيل الدخول."
        else:
            reason = "خطأ غير معروف أثناء التحميل."
        await update.message.reply_text(f"❌ تعذر تحميل الفيديو: {reason}")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ غير متوقع:\n{e}")

# تشغيل البوت
if __name__ == "__main__":
    TOKEN = "8547768233:AAFqr2dIJ5OhQ5T0h9EiwpNrIc9zKBV7SAs"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("البوت يعمل الآن...")
    app.run_polling()
