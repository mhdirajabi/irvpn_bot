import asyncio
from datetime import datetime, timedelta

from services.api_client import APIClient
from services.order_service import update_order
from services.user_service import get_subscription_info
from utils.logger import logger


async def check_pending_orders(bot):
    while True:
        try:
            orders = await APIClient.get("/orders/", params={"status": "pending"})
            for order in orders:
                created_time = datetime.fromisoformat(order["created_at"])
                if datetime.now() - created_time > timedelta(minutes=30):
                    await update_order(order["order_id"], {"status": "rejected"})
                    await bot.send_message(
                        order["telegram_id"],
                        f"سفارش *{order['order_id']}* به دلیل عدم ارسال رسید در 30 دقیقه لغو شد.",
                        parse_mode="Markdown",
                    )
        except Exception as e:
            logger.error(f"Error checking pending orders: {e}")
        await asyncio.sleep(60)


async def check_expiring_users(bot):
    while True:
        try:
            users = await APIClient.get("/users/")
            for user in users:
                token = user["subscription_token"]
                if token:
                    user_info = await get_subscription_info(token)
                    if user_info and user_info.get("expire"):
                        expire_time = datetime.fromtimestamp(user_info["expire"])
                        days_left = (expire_time - datetime.now()).days
                        if days_left in [1, 3, 7]:
                            await bot.send_message(
                                user["telegram_id"],
                                f"اکانت شما (*{user['username']}*) {days_left} روز دیگه منقضی می‌شه! "
                                "برای تمدید از /renew استفاده کنید.",
                                parse_mode="Markdown",
                            )
        except Exception as e:
            logger.error(f"Error checking expiring users: {e}")
        await asyncio.sleep(3600)
