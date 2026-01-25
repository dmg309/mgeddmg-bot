# bot_downloader.py
# شغّله: python bot_downloader.py

import logging
import os
import tempfile
import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import yt_dlp

# ────────────────────────────────────────────────
TOKEN = "8546899518:AAG8DJc6HV6pffpiGBpzrUf-HawRZts3zvA"
# ────────────────────────────────────────────────

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

WELCOME_MESSAGES = [
    "مرحبا يا {name} 👋 جاهز أحمل لك أي فيديو تبيه؟",
    "أهلين {name} 🔥 ارمي الرابط وخليني أشتغل!",
    "يا هلا والله {name} 📥 وش تبي نحمله اليوم؟",
    "مرحباً بـ {name} في عالم التحميل السريع 😈",
    "هلا {name}! يلا وريني الرابط اللي مخبيه...",
]

LOADING_MESSAGES = [
    "جاري التحميل يا {name}... انتظر شوي ⏳",
    "خلاص يا {name}، ماسك الرابط وأنا أجيبه لك 🔥",
    "يلا يا {name}، البوت شغال بقوة الآن 💪",
    "ثواني بس يا {name}... الفيديو في الطريق 📡",
]

SUCCESS_MESSAGES = [
    "هاك يا {name}، نزلته لك نظيف 📥",
    "جاهز يا {name}! استمتع بالفيديو 😎",
    "خلصت يا {name}، حمل ولا تقلي شكراً 😂",
    "تفضل يا {name}، الفيديو على طبق من ذهب ✨",
]

ERROR_AGE_MESSAGES = [
    "يا {name}، الفيديو مقيد بالعمر 😕 جرب فيديو عام أو غيّر الحساب",
    "معليش يا {name}، يوتيوب يبي تسجيل دخول عشان العمر...",
]

ERROR_GEO_MESSAGES = [
    "يا {name}، الفيديو غير متاح في منطقتك 🚫 جرب VPN",
    "الفيديو محجوب جغرافياً يا {name} 😔",
]

GENERAL_ERROR_MESSAGES = [
    "معليش يا {name}، ما قدرت أحمله 😔 الرابط ممكن غلط أو المحتوى مقيد",
    "حصل خطأ يا {name} 😅 جرب رابط ثاني أو انتظر شوي",
]

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
    'outtmpl': '%(title)s.%(ext)s',
    'noplaylist': True,
    'continuedl': True,
    'no_check_certificate': True,
}

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    name = user.first_name or "الغالي"
    msg = random.choice(WELCOME_MESSAGES).format(name=name)
    update.message.reply_text(msg)

def help_command(update: Update, context: CallbackContext):
    user = update.effective_user
    name = user.first_name or "الغالي"
    text = (
        f"يا {name}، البوت يساعدك تحمل فيديوهات من:\n"
        "• يوتيوب\n• تيك توك\n• إنستغرام\n• تويتر/X\n• سناب (أحياناً)\n"
        "وكثير مواقع ثانية 📹\n\n"
        "ارسل الرابط مباشرة وسأحمله لك 😎"
    )
    update.message.reply_text(text)

def download_video(update: Update, context: CallbackContext):
    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):
        update.message.reply_text("يا بعدي، أرسل رابط يبدأ بـ http أو https من فضلك 😅")
        return

    user = update.effective_user
    name = user.first_name or "الغالي"

    loading_text = random.choice(LOADING_MESSAGES).format(name=name)
    status_msg = update.message.reply_text(loading_text)

    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            ydl_opts['outtmpl'] = os.path.join(tmpdirname, '%(title)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            if not os.path.exists(filename):
                status_msg.edit_text(f"يا {name}، تعذّر العثور على الملف بعد التحميل 😕")
                return

            file_size_mb = os.path.getsize(filename) / (1024 * 1024)

            if file_size_mb > 50:
                status_msg.edit_text(
                    f"يا {name}، الفيديو كبير جدًا ({file_size_mb:.1f} ميجا)\n"
                    "تليجرام يحدد 50 ميجا للبوتات العادية.\nجرب رابط أقصر."
                )
                return

            status_msg.edit_text("جاري الإرسال... 📤")

            with open(filename, 'rb') as video_file:
                update.message.reply_document(
                    document=video_file,
                    caption=f"تم التحميل: {info.get('title', 'فيديو')}\n{url}",
                    filename=os.path.basename(filename)
                )

            success_text = random.choice(SUCCESS_MESSAGES).format(name=name)
            update.message.reply_text(success_text)

            status_msg.delete()

    except Exception as e:
        status_msg.edit_text(f"حصل خطأ يا {name} 😢\nجرب مرة ثانية")
        logger.error(e)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))

    print("البوت يعمل...")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
    
