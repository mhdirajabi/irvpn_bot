import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import DJANGO_API_URL
from services.api_client import APIClient
from services.order_service import update_order
from services.user_service import get_subscription_info
from utils.logger import logger


async def check_pending_orders(bot):
    while True:
        try:
            logger.info("Checking pending orders...")
            orders = await APIClient.get(
                "/orders/", params={"status": "pending"}, base_url=DJANGO_API_URL
            )
            now = datetime.now(ZoneInfo("UTC"))
            for order in orders:
                try:
                    created_time = datetime.fromisoformat(
                        order["created_at"].replace("Z", "+00:00")
                    )
                    if now - created_time > timedelta(minutes=30):
                        try:
                            await update_order(
                                order["order_id"], {"status": "rejected"}
                            )
                            await bot.send_message(
                                order["telegram_id"],
                                f"سفارش *{order['order_id']}* به دلیل عدم ارسال رسید در 30 دقیقه لغو شد.",
                                parse_mode="Markdown",
                            )
                            logger.info(
                                f"Order {order['order_id']} rejected and user {order['telegram_id']} notified"
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to reject order {order['order_id']} or notify user {order['telegram_id']}: {e}"
                            )
                except Exception as e:
                    logger.error(
                        f"Error processing order {order.get('order_id', 'unknown')}: {e}"
                    )
        except Exception as e:
            logger.error(f"Error checking pending orders: {e}")
        logger.info("Finished checking pending orders, sleeping for 1 minute...")
        await asyncio.sleep(60)


async def check_expiring_users(bot):
    while True:
        try:
            logger.info("Checking expiring users...")
            users = await APIClient.get("/users/", base_url=DJANGO_API_URL)
            now = datetime.now(ZoneInfo("UTC"))
            for user in users:
                try:
                    if "subscription_token" not in user:
                        logger.warning(
                            f"User {user.get('telegram_id', 'unknown')} has no subscription_token"
                        )
                        continue
                    token = user["subscription_token"]
                    if not token:
                        logger.debug(
                            f"Empty subscription_token for user {user.get('telegram_id', 'unknown')}"
                        )
                        continue
                    user_info = await get_subscription_info(token)
                    if not user_info or not user_info.get("expire"):
                        logger.debug(
                            f"No expiration info for user {user.get('telegram_id', 'unknown')}"
                        )
                        continue
                    expire_time = datetime.fromtimestamp(
                        user_info["expire"], tz=ZoneInfo("UTC")
                    )
                    days_left = (expire_time - now).days
                    if days_left in [1, 3, 7]:
                        try:
                            await bot.send_message(
                                user["telegram_id"],
                                f"اکانت شما (*{user['username']}*) {days_left} روز دیگه منقضی می‌شه! "
                                "برای تمدید از /renew استفاده کنید.",
                                parse_mode="Markdown",
                            )
                            logger.info(
                                f"Sent expiration warning to user {user['telegram_id']} ({days_left} days left)"
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to send message to user {user['telegram_id']}: {e}"
                            )
                except Exception as e:
                    logger.error(
                        f"Error processing user {user.get('telegram_id', 'unknown')}: {e}"
                    )
        except Exception as e:
            logger.error(f"Error checking expiring users: {e}")
        logger.info("Finished checking expiring users, sleeping for 1 hour...")
        await asyncio.sleep(3600)
