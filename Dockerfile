# اختر صورة Python الرسمية
FROM python:3.13-slim

# تثبيت FFmpeg والأدوات الضرورية
RUN apt-get update && \
    apt-get install -y ffmpeg curl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# إنشاء مجلد العمل
WORKDIR /app

# نسخ الملفات
COPY requirements.txt .
COPY bot.py .
COPY cookies.txt .   # ملف Cookies من متصفحك

# تثبيت المكتبات
RUN pip install --no-cache-dir -r requirements.txt

# أمر تشغيل البوت
CMD ["python", "bot.py"]
