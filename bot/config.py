import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@YourChannel")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MARZBAN_API_URL = os.getenv("MARZBAN_API_URL")
MARZBAN_API_TOKEN = os.getenv("MARZBAN_API_TOKEN")
DB_DSN = os.getenv("DB_DSN")
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/path/to/media")
