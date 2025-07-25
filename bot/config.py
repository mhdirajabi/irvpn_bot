import os

from dotenv import load_dotenv

load_dotenv()

ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "123456789"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "default_password")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/")
BOT_TOKEN = os.getenv("BOT_TOKEN", "default_bot_token")
CARD_NUMBER = os.getenv("CARD_NUMBER", "1234-5678-9012-3456")
CARD_HOLDER = os.getenv("CARD_HOLDER", "Default Card Holder")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@default_channel")
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8001/api/")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/path/to/media")
