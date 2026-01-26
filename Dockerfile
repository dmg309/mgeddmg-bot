# استخدم صورة Python الرسمية
FROM python:3.13-slim

# تثبيت أدوات النظام المطلوبة
RUN apt-get update && \
    apt-get install -y ffmpeg curl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# إنشاء مجلد العمل
WORKDIR /app

# نسخ ملفات المشروع
COPY requirements.txt .
COPY bot.py .

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# تعيين الأمر الرئيسي لتشغيل البوت
CMD ["python", "bot.py"]
