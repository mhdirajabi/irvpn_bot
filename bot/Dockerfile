# استفاده از نسخه سبک پایتون 3.12
FROM python:3.12-slim

# تنظیم دایرکتوری کاری
WORKDIR /app

# کپی کردن فایل‌های پروژه
COPY . .

# نصب وابستگی‌ها
RUN pip install --no-cache-dir -r requirements.txt

# تنظیم دستور اجرا
CMD ["python", "main.py"]