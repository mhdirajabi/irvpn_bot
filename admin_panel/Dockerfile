# استفاده از نسخه سبک پایتون 3.12
FROM python:3.12-slim

# تنظیم دایرکتوری کاری
WORKDIR /app

# کپی کردن فایل‌های پروژه
COPY . .

# نصب وابستگی‌ها
RUN pip install --no-cache-dir -r requirements.txt

# جمع‌آوری فایل‌های استاتیک
RUN python manage.py collectstatic --noinput

# تنظیم دستور اجرا با Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "admin_panel.wsgi:application"]