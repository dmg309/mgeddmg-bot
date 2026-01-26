import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp.utils import DownloadError, UnsupportedError

# مجلد مؤقت للتحميل
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

MAX_FILE_SIZE_MB = 50  # الحد الأقصى للحجم المسموح به على Telegram

def get_ydl_opts(user, force_low_quality=False):
    # إذا الفيديو كبير، نخفض الجودة
    format_choice = 'bestvideo+bestaudio/best'
    if force_low_quality:
        format_choice = 'bv[height<=480]+ba/best[height<=480]/best'

    return {
        'format': format_choice,
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, f'%(title)s-{user}.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        }
    }

def is_supported_url(url: str) -> bool:
    supported_domains = ['youtube.com', 'youtu.be', 'tiktok.com', 'vimeo.com']
    return any(domain in url for domain in supported_domains)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أرسل رابط فيديو من YouTube أو TikTok أو Vimeo لتحميله.\n"
        "سيتم تقليل جودة الفيديو تلقائيًا إذا كان حجمه كبيرًا."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user = update.message.from_user.username or update.message.from_user.first_name

    if not is_supported_url(url):
        await update.message.reply_text("❌ هذا الرابط غير مدعوم.")
        return

    await update.message.reply_text("⏳ جاري تحميل الفيديو...")

    force_low_quality = False

    try:
        ydl_opts = get_ydl_opts(user, force_low_quality)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # التحقق من حجم الفيديو
        size_mb = os.path.getsize(filename) / (1024*1024)
        if size_mb > MAX_FILE_SIZE_MB:
            # إعادة تحميل الفيديو بجودة منخفضة
            await update.message.reply_text(
                f"⚠️ حجم الفيديو {size_mb:.2f}MB، سيتم تنزيل نسخة بجودة أقل..."
            )
            force_low_quality = True
            ydl_opts = get_ydl_opts(user, force_low_quality)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

        # إرسال الفيديو
        with open(filename, "rb") as video_file:
            await update.message.reply_video(video_file, caption=f"✅ تم تحميل الفيديو: {info.get('title')}")

        os.remove(filename)

    except UnsupportedError:
        await update.message.reply_text(
            "❌ الرابط غير مدعوم للتحميل. ربما رابط صورة أو فيديو خاص."
        )
    except DownloadError as e:
        msg = str(e)
        if "HTTP Error 503" in msg:
            reason = "الخادم غير متاح مؤقتًا (HTTP 503). حاول لاحقًا."
        elif "Private" in msg or "Login" in msg:
            reason = "الفيديو خاص أو يتطلب تسجيل الدخول."
        else:
            reason = "خطأ أثناء التحميل."
        await update.message.reply_text(f"❌ تعذر تحميل الفيديو: {reason}")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ غير متوقع:\n{e}")

if __name__ == "__main__":
    TOKEN = "8547768233:AAFqr2dIJ5OhQ5T0h9EiwpNrIc9zKBV7SAs"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("البوت يعمل الآن...")
    app.run_polling()
