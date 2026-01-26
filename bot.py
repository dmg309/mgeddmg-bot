import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# تضع هنا توكن البوت
TOKEN = "8547768233:AAFqr2dIJ5OhQ5T0h9EiwpNrIc9zKBV7SAs"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أرسل رابط الفيديو ليتم تحميله.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    user_name = update.message.from_user.first_name

    # تحقق سريع من أن الرسالة تحتوي رابط
    if not message.startswith("http"):
        await update.message.reply_text("الرجاء إرسال رابط صالح للفيديو.")
        return

    await update.message.reply_text(f"جارٍ تحميل الفيديو باسم {user_name}...")

    filename = f"{user_name}_video.%(ext)s"
    ydl_opts = {
        'format': 'best',  # تحميل أفضل نسخة متاحة (فيديو وصوت مدمجين)
        'outtmpl': filename,
        'noplaylist': True,
        'quiet': True,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(message, download=True)
            if info is None:
                await update.message.reply_text("فشل التحميل: الرابط غير صالح أو محمي.")
                return

            # الحصول على اسم الملف النهائي
            downloaded_file = ydl.prepare_filename(info)

            # تحقق من حجم الملف
            if not os.path.exists(downloaded_file) or os.path.getsize(downloaded_file) < 1000:
                await update.message.reply_text("تم تحميل ملف فارغ أو الرابط غير صالح!")
                return

            # إرسال الفيديو للمستخدم
            await update.message.reply_video(video=open(downloaded_file, 'rb'), caption=f"تم تحميل الفيديو بنجاح باسم {user_name}!")

            # حذف الملف بعد الإرسال لتوفير مساحة
            os.remove(downloaded_file)

    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء التحميل: {str(e)}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
