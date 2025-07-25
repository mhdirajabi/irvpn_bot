import asyncio
import uuid
from datetime import datetime, timedelta

import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from config import (
    ADMIN_TELEGRAM_ID,
    API_BASE_URL,
    BOT_TOKEN,
    CARD_HOLDER,
    CARD_NUMBER,
    CHANNEL_ID,
    DJANGO_API_URL,
)
from utils.logger import logger
from utils.marzban import API_TOKEN
from utils.plans import PLANS

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def check_channel_membership(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


async def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_TELEGRAM_ID


def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📊 وضعیت اکانت"),
                KeyboardButton(text="🛒 خرید اکانت"),
            ],
            [
                KeyboardButton(text="🔄 تمدید اکانت"),
                KeyboardButton(text="🔗 دریافت لینک"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard


def get_main_menu_inline():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 وضعیت اکانت", callback_data="main_status"
                ),
                InlineKeyboardButton(text="🛒 خرید اکانت", callback_data="main_buy"),
            ],
            [
                InlineKeyboardButton(text="🔄 تمدید اکانت", callback_data="main_renew"),
                InlineKeyboardButton(
                    text="🔗 دریافت لینک", callback_data="main_getlink"
                ),
            ],
        ]
    )
    return keyboard


def save_user_token(telegram_id: int, token: str, username: str):
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/users/",
            json={
                "telegram_id": telegram_id,
                "subscription_token": token,
                "username": username,
            },
            timeout=2000,
        )
        if response.status_code != 200:
            print(f"Error syncing user with Django: {response.text}")
    except Exception as e:
        print(f"Error syncing user with Django: {e}")


def get_user_data(telegram_id: int) -> tuple:
    try:
        response = requests.get(
            f"{DJANGO_API_URL}/users?telegram_id={telegram_id}",
            timeout=2000,
        )
        if response.status_code == 200:
            users = response.json()
            if users:
                return (users[0]["subscription_token"], users[0]["username"])
        return (None, None)
    except Exception as e:
        print(f"Error fetching user from Django: {e}")
        return (None, None)


def save_order(
    telegram_id: int,
    order_id: str,
    plan_id: str,
    plan_type: str,
    price: int,
    is_renewal: bool = False,
):
    data = {
        "telegram_id": telegram_id,
        "order_id": order_id,
        "plan_id": f"{plan_type}:{plan_id}",
        "status": "pending",
        "price": price,
        "is_renewal": is_renewal,
    }
    logger.debug(f"Sending order to Django: {data}")
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/orders/",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=5,
            verify=True,
        )
        response.raise_for_status()
        logger.info(
            f"Order saved successfully: {order_id}, response: {response.json()}"
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Error syncing order with Django: {e}, response: {response.text if 'response' in locals() else 'No response'}"
        )
        raise Exception(f"Failed to save order: {e}") from e


def update_order_status(
    order_id: str, status: str, receipt_url: str = None, receipt_message_id: int = None
):
    try:
        response = requests.put(
            f"{DJANGO_API_URL}/orders/{order_id}/",
            json={
                "status": status,
                "receipt_url": receipt_url,
                "receipt_message_id": receipt_message_id,
            },
            timeout=2000,
        )
        if response.status_code != 200:
            print(f"Error syncing order status with Django: {response.text}")
    except Exception as e:
        print(f"Error syncing order status with Django: {e}")


def get_subscription_info(token: str):
    response = requests.get(
        f"{API_BASE_URL}/sub/{token}/info",
        timeout=2000,
    )
    if response.status_code == 200:
        return response.json()
    return None


def create_user(
    username: str,
    data_limit: int,
    expire_days: int,
    users: str,
    telegram_id: int = None,
):
    logger.debug(
        f"Creating user {username} with data_limit={data_limit}, expire_days={expire_days}, users={users}"
    )
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }
    expire_timestamp = (
        0
        if expire_days == 0
        else int((datetime.now() + timedelta(days=expire_days)).timestamp())
    )
    inbounds = {"vless": ["IR_SV"]}
    if users == "double":
        inbounds = {"vless": ["IR_SV", "SERVER-KHAREJ"]}

    payload = {
        "username": username,
        "proxies": {"vless": {}},
        "inbounds": inbounds,
        "data_limit": data_limit if data_limit else None,
        "expire": expire_timestamp,
        "status": "active",
        "data_limit_reset_strategy": "no_reset",
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/user",
            json=payload,
            headers=headers,
            timeout=5,
            verify=True,
        )
        response.raise_for_status()
        user_info = response.json()
        logger.info(f"User {username} created successfully: {user_info}")
        try:
            django_payload = {
                "telegram_id": telegram_id,
                "username": username,
                "data_limit": data_limit,
                "expire": expire_timestamp,
                "status": "active",
                "data_limit_reset_strategy": "no_reset",
                "subscription_url": user_info.get("subscription_url", ""),
            }
            django_response = requests.post(
                f"{DJANGO_API_URL}/users/",
                json=django_payload,
                headers={"Content-Type": "application/json"},
                timeout=5,
                verify=True,
            )
            django_response.raise_for_status()
            logger.info(f"User {username} saved in Django: {django_response.json()}")
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to save user {username} in Django: {e}, response: {django_response.text if 'django_response' in locals() else 'No response'}"
            )
        return user_info
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Failed to create user {username}: {e}, response: {response.text if 'response' in locals() else 'No response'}"
        )
        return None


def renew_user(
    username: str,
    data_limit: int,
    expire_days: int,
    users: str,
    telegram_id: int = None,
):
    logger.debug(
        f"Renewing user {username} with data_limit={data_limit}, expire_days={expire_days}, users={users}"
    )
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }
    expire_timestamp = (
        0
        if expire_days == 0
        else int((datetime.now() + timedelta(days=expire_days)).timestamp())
    )
    inbounds = {"vless": ["IR_SV"]}
    if users == "double":
        inbounds = {"vless": ["IR_SV", "SERVER-KHAREJ"]}

    payload = {
        "data_limit": data_limit if data_limit else None,
        "expire": expire_timestamp,
        "inbounds": inbounds,
        "status": "active",
        "data_limit_reset_strategy": "no_reset",
    }

    try:
        response = requests.put(
            f"{API_BASE_URL}/api/user/{username}",
            json=payload,
            headers=headers,
            timeout=5,
            verify=True,
        )
        response.raise_for_status()
        user_info = response.json()
        logger.info(f"User {username} renewed successfully: {user_info}")
        try:
            django_payload = {
                "telegram_id": telegram_id,
                "username": username,
                "data_limit": data_limit,
                "expire": expire_timestamp,
                "status": "active",
                "data_limit_reset_strategy": "no_reset",
                "subscription_url": user_info.get("subscription_url", ""),
            }
            django_response = requests.put(
                f"{DJANGO_API_URL}/users/{username}",
                json=django_payload,
                headers={"Content-Type": "application/json"},
                timeout=5,
                verify=True,
            )
            django_response.raise_for_status()
            logger.info(f"User {username} updated in Django: {django_response.json()}")
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to update user {username} in Django: {e}, response: {django_response.text if 'django_response' in locals() else 'No response'}"
            )
        return user_info
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Failed to renew user {username}: {e}, response: {response.text if 'response' in locals() else 'No response'}"
        )
        return None


async def check_pending_orders():
    while True:
        try:
            response = requests.get(
                f"{DJANGO_API_URL}/orders?status=pending",
                timeout=2,
            )
            if response.status_code == 200:
                orders = response.json()
                for order in orders:
                    created_time = datetime.fromisoformat(order["created_at"])
                    if datetime.now() - created_time > timedelta(minutes=30):
                        update_order_status(order["order_id"], "rejected")
                        await bot.send_message(
                            order["telegram_id"],
                            f"سفارش {order['order_id']} به دلیل عدم ارسال رسید در 30 دقیقه لغو شد.",
                        )
        except Exception as e:
            print(f"Error checking pending orders: {e}")
        await asyncio.sleep(60)


async def check_expiring_users():
    while True:
        try:
            response = requests.get(
                f"{DJANGO_API_URL}/users/",
                timeout=2,
            )
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    token = user["subscription_token"]
                    if token:
                        user_info = get_subscription_info(token)
                        if user_info and user_info.get("expire"):
                            expire_time = datetime.fromtimestamp(user_info["expire"])
                            days_left = (expire_time - datetime.now()).days
                            if days_left in [1, 3, 7]:
                                await bot.send_message(
                                    user["telegram_id"],
                                    f"اکانت شما ({user['username']}) {days_left} روز دیگه منقضی می‌شه! "
                                    "برای تمدید از /renew استفاده کنید.",
                                )
        except Exception as e:
            print(f"Error checking expiring users: {e}")
        await asyncio.sleep(3600)


@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    if not await check_channel_membership(user_id):
        await message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}\n"
            "بعد از عضویت، دوباره /start رو بزنید.",
            parse_mode="Markdown",
        )
        return

    is_admin_user = await is_admin(user_id)
    reply = (
        "*به ربات IRVPN خوش اومدی!* 😊\n"
        "لطفاً یکی از گزینه‌های زیر رو انتخاب کن:\n\n"
        f"{'*دستورات ادمین*:\n/adduser - ایجاد کاربر جدید\n/servers - مدیریت سرورها\n' if is_admin_user else ''}"
        "📊 *وضعیت اکانت*: بررسی وضعیت اشتراک\n"
        "🛒 *خرید اکانت*: خرید اکانت جدید\n"
        "🔄 *تمدید اکانت*: تمدید اشتراک موجود\n"
        "🔗 *دریافت لینک*: دریافت لینک اشتراک"
    )
    await message.reply(reply, parse_mode="Markdown", reply_markup=get_main_menu())


@dp.message(Command("settoken"))
async def settoken_command(message: types.Message):
    user_id = message.from_user.id
    if not await check_channel_membership(user_id):
        await message.reply(f"لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply(
            "لطفاً کد اشتراک (token) رو وارد کنید:\n/settoken <your_token>"
        )
        return

    token = args[1]
    user_info = get_subscription_info(token)
    if user_info:
        save_user_token(user_id, token, user_info["username"])
        await message.reply(
            "کد اشتراک ذخیره شد! حالا می‌تونی از /status یا /getlink استفاده کنی."
        )
    else:
        await message.reply("کد اشتراک نامعتبره! لطفاً دوباره امتحان کن.")


@dp.message(lambda message: message.text == "📊 وضعیت اکانت")
@dp.message(Command("status"))
async def status_command(message: types.Message):
    telegram_id = message.from_user.id
    try:
        response = requests.get(
            f"{DJANGO_API_URL}/users/?telegram_id={telegram_id}",
            timeout=5,
            verify=True,
        )
        response.raise_for_status()
        users = response.json()
        if not users:
            await message.answer(
                "⚠️ *هیچ اکانتی برای شما پیدا نشد!*", parse_mode="Markdown"
            )
            return
        user = users[0]
        await message.answer(
            f"*وضعیت اکانت شما:* 📋\n"
            f"👤 *نام کاربری*: {user['username']}\n"
            f"📈 *حجم*: {user['data_limit'] / 1073741824 if user['data_limit'] else '♾️ نامحدود'} گیگابایت\n"
            f"⏳ *انقضا*: {datetime.fromtimestamp(user['expire']).strftime('%Y-%m-%d') if user['expire'] else '♾️ لایف‌تایم'}\n"
            f"✅ *وضعیت*: {user['status']}",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
    except requests.exceptions.RequestException as e:
        await message.answer("❌ *خطا در دریافت اطلاعات اکانت!*", parse_mode="Markdown")
        logger.error(f"Failed to fetch user status for telegram_id={telegram_id}: {e}")


@dp.message(Command("getlink"))
async def getlink_command(message: types.Message):
    telegram_id = message.from_user.id
    try:
        response = requests.get(
            f"{DJANGO_API_URL}/users/?telegram_id={telegram_id}",
            timeout=5,
            verify=True,
        )
        response.raise_for_status()
        users = response.json()
        if not users:
            await message.answer("هیچ اکانتی برای شما پیدا نشد!")
            return
        user = users[0]
        if user.get("subscription_url"):
            await message.answer(f"لینک اشتراک شما:\n{user['subscription_url']}")
        else:
            await message.answer("لینک اشتراک برای شما وجود ندارد!")
    except requests.exceptions.RequestException as e:
        await message.answer("خطا در دریافت لینک اشتراک!")
        logger.error(
            f"Failed to fetch subscription link for telegram_id={telegram_id}: {e}"
        )


@dp.callback_query(lambda c: c.data.startswith("getlink_"))
async def process_client_type(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await check_channel_membership(user_id):
        await callback.message.reply(f"لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}")
        return

    client_type, token = callback.data.split("_")[1:3]
    response = requests.get(f"{API_BASE_URL}/sub/{token}/{client_type}", timeout=2000)
    if response.status_code == 200:
        await callback.message.reply(f"لینک اشتراک ({client_type}):\n{response.text}")
    else:
        await callback.message.reply("خطا در دریافت لینک اشتراک!")
    await callback.answer()


@dp.message(Command("adduser"))
async def adduser_command(message: types.Message):
    user_id = message.from_user.id
    if not await check_channel_membership(user_id):
        await message.reply(f"لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}")
        return

    if not await is_admin(user_id):
        await message.reply("این دستور فقط برای ادمین‌ها قابل استفاده است!")
        return

    args = message.text.split(maxsplit=4)
    if len(args) < 5:
        await message.reply(
            "لطفاً اطلاعات کاربر رو وارد کنید:\n"
            "/adduser <username> <data_limit_in_GB> <expire_days> <users>\n"
            "مثال: /adduser user123 10 30 unlimited"
        )
        return

    username, data_limit, expire_days, users = args[1:5]
    try:
        data_limit = float(data_limit) * 1073741824 if data_limit != "0" else 0
        user_info = create_user(username, int(data_limit), int(expire_days), users)
        if user_info:
            save_user_token(
                user_id, user_info["subscription_url"].split("/")[-2], username
            )
            await message.reply(
                f"کاربر {username} با موفقیت ایجاد شد! Token: {user_info['subscription_url'].split('/')[-2]}"
            )
        else:
            await message.reply("خطا در ایجاد کاربر!")
    except Exception as e:
        await message.reply(f"خطا: {str(e)}")


@dp.message(Command("servers"))
async def servers_command(message: types.Message):
    user_id = message.from_user.id
    if not await check_channel_membership(user_id):
        await message.reply(f"لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}")
        return

    if not await is_admin(user_id):
        await message.reply("این دستور فقط برای ادمین‌ها قابل استفاده است!")
        return

    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(f"{API_BASE_URL}/api/nodes", headers=headers, timeout=2000)
    if response.status_code == 200:
        nodes = response.json()
        reply = "لیست سرورها:\n"
        for node in nodes:
            reply += (
                f"ID: {node['id']}, Name: {node['name']}, Status: {node['status']}\n"
            )
        await message.reply(reply)
    else:
        await message.reply(f"خطا در دریافت لیست سرورها: {response.text}")


@dp.message(lambda message: message.text == "🛒 خرید اکانت")
@dp.message(Command("buy"))
async def buy_command(message: types.Message):
    user_id = message.from_user.id
    if not await check_channel_membership(user_id):
        await message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}", parse_mode="Markdown"
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📈 اکانت حجمی", callback_data="buy_volume")],
            [
                InlineKeyboardButton(
                    text="♾️ اکانت نامحدود", callback_data="buy_unlimited"
                )
            ],
            [InlineKeyboardButton(text="🧪 اکانت تست", callback_data="buy_test")],
            [
                InlineKeyboardButton(
                    text="⬅️ بازگشت به منوی اصلی", callback_data="back_to_main"
                )
            ],
        ]
    )
    await message.reply(
        "*لطفاً نوع اکانت را انتخاب کنید:*", parse_mode="Markdown", reply_markup=keyboard
    )


@dp.callback_query(lambda c: c.data == "buy_back")
async def buy_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "*لطفاً نوع اکانت را انتخاب کنید:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📈 اکانت حجمی", callback_data="buy_volume"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="♾️ اکانت نامحدود", callback_data="buy_unlimited"
                    )
                ],
                [InlineKeyboardButton(text="🧪 اکانت تست", callback_data="buy_test")],
                [
                    InlineKeyboardButton(
                        text="⬅️ بازگشت به منوی اصلی", callback_data="back_to_main"
                    )
                ],
            ]
        ),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "*به منوی اصلی خوش اومدی!* 😊\nلطفاً یک گزینه انتخاب کن:",
        parse_mode="Markdown",
        reply_markup=get_main_menu_inline(),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def process_account_type(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await check_channel_membership(user_id):
        await callback.message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
        )
        return

    account_type = callback.data.split("_")[1]
    plans = PLANS.get(account_type, {})
    if not plans:
        await callback.message.reply(
            "❌ *نوع اکانت نامعتبر است!*", parse_mode="Markdown"
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📦 پلن {plan_id}: {plan['data_limit'] / 1073741824 if plan['data_limit'] else '♾️ نامحدود'} گیگ، "
                    f"{plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز، {plan['price']} تومان",
                    callback_data=f"select_{account_type}_{plan_id}",
                )
            ]
            for plan_id, plan in plans.items()
        ]
        + [[InlineKeyboardButton(text="⬅️ بازگشت", callback_data="buy_back")]]
    )
    await callback.message.edit_text(
        f"*لطفاً پلن {account_type} مورد نظر را انتخاب کنید:*",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("select_"))
async def process_plan_selection(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await check_channel_membership(user_id):
        await callback.message.reply(f"لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}")
        return

    _, account_type, plan_id = callback.data.split("_")
    plan = PLANS.get(account_type, {}).get(plan_id)
    if not plan:
        await callback.message.reply("پلن نامعتبر است!")
        return

    if plan["price"] == 0:  # اکانت تست رایگان
        username = f"user_{uuid.uuid4().hex[:8]}"
        user_info = create_user(
            username, plan["data_limit"], plan["expire_days"], plan["users"]
        )
        if user_info:
            token = user_info["subscription_url"].split("/")[-2]
            save_user_token(user_id, token, username)
            await callback.message.reply(
                f"اکانت تست شما ایجاد شد!\n"
                f"نام کاربری: {username}\n"
                f"حجم: {plan['data_limit'] / 1073741824} گیگابایت\n"
                f"مدت: {plan['expire_days']} روز\n"
                f"لینک اشتراک: {user_info['subscription_url']}\n"
                f"لطفاً این لینک را ذخیره کنید یا از /getlink برای دریافت مجدد استفاده کنید."
            )
        else:
            await callback.message.reply("خطا در ایجاد اکانت تست!")
        await callback.answer()
        return

    order_id = str(uuid.uuid4())
    save_order(user_id, order_id, plan_id, account_type, plan["price"])

    await callback.message.reply(
        f"شما پلن {plan_id} ({account_type}) را انتخاب کردید:\n"
        f"حجم: {plan['data_limit'] / 1073741824 if plan['data_limit'] else 'نامحدود'} گیگابایت\n"
        f"مدت: {plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز\n"
        f"مبلغ: {plan['price']} تومان\n\n"
        f"لطفاً مبلغ را به شماره کارت زیر واریز کنید و رسید را ظرف 30 دقیقه ارسال کنید:\n"
        f"شماره کارت: {CARD_NUMBER} (به نام {CARD_HOLDER})\n\n"
        f"برای ارسال رسید، کافیست عکس رسید را در همین چت بفرستید."
    )
    await callback.answer()


@dp.message(Command("renew"))
async def renew_command(message: types.Message):
    user_id = message.from_user.id
    if not await check_channel_membership(user_id):
        await message.reply(f"لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}")
        return

    token, username = get_user_data(user_id)
    if not username:
        await message.reply("لطفاً اول کد اشتراک رو با /settoken وارد کنید.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="اکانت حجمی", callback_data="renew_volume")],
            [
                InlineKeyboardButton(
                    text="اکانت نامحدود", callback_data="renew_unlimited"
                )
            ],
        ]
    )
    await message.reply(
        "لطفاً نوع اکانت برای تمدید را انتخاب کنید:", reply_markup=keyboard
    )


@dp.callback_query(lambda c: c.data.startswith("renew_"))
async def process_renew_type(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await check_channel_membership(user_id):
        await callback.message.reply(f"لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}")
        return

    account_type = callback.data.split("_")[1]
    plans = PLANS.get(account_type, {})
    if not plans:
        await callback.message.reply("نوع اکانت نامعتبر است!")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"پلن {plan_id}: {plan['data_limit'] / 1073741824 if plan['data_limit'] else 'نامحدود'} گیگ، "
                    f"{plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز، {plan['price']} تومان",
                    callback_data=f"renewselect_{account_type}_{plan_id}",
                )
            ]
            for plan_id, plan in plans.items()
        ]
    )
    await callback.message.reply(
        f"لطفاً پلن {account_type} برای تمدید را انتخاب کنید:", reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("renewselect_"))
async def process_renew_plan_selection(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await check_channel_membership(user_id):
        await callback.message.reply(f"لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}")
        return

    _, account_type, plan_id = callback.data.split("_")
    plan = PLANS.get(account_type, {}).get(plan_id)
    if not plan:
        await callback.message.reply("پلن نامعتبر است!")
        return

    order_id = str(uuid.uuid4())
    save_order(user_id, order_id, plan_id, account_type, plan["price"], is_renewal=True)

    await callback.message.reply(
        f"شما پلن {plan_id} ({account_type}) برای تمدید انتخاب کردید:\n"
        f"حجم: {plan['data_limit'] / 1073741824 if plan['data_limit'] else 'نامحدود'} گیگابایت\n"
        f"مدت: {plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز\n"
        f"مبلغ: {plan['price']} تومان\n\n"
        f"لطفاً مبلغ را به شماره کارت زیر واریز کنید و رسید را ظرف 30 دقیقه ارسال کنید:\n"
        f"شماره کارت: {CARD_NUMBER} (به نام {CARD_HOLDER})\n\n"
        f"برای ارسال رسید، کافیست عکس رسید را در همین چت بفرستید."
    )
    await callback.answer()


@dp.message(F.photo)
async def handle_receipt(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    logger.debug(f"Handling receipt for user: {user_id}")
    if not await check_channel_membership(user_id):
        logger.warning(f"User {user_id} not in channel {CHANNEL_ID}")
        await message.reply(f"لطفاً ابتدا در کانال ما عضو شوید: {CHANNEL_ID}")
        return

    try:
        url = f"{DJANGO_API_URL}/orders/?telegram_id={user_id}&status=pending"
        logger.debug(f"Sending GET request to: {url}")
        response = requests.get(url, timeout=5, verify=True)
        response.raise_for_status()
        orders = response.json()
        logger.info(f"Orders fetched for user {user_id}: {orders}")
        if not orders:
            logger.warning(f"No pending orders found for user {user_id}")
            all_orders_response = requests.get(
                f"{DJANGO_API_URL}/orders/?telegram_id={user_id}",
                timeout=5,
                verify=True,
            )
            all_orders = (
                all_orders_response.json()
                if all_orders_response.status_code == 200
                else []
            )
            logger.debug(f"All orders for user {user_id}: {all_orders}")
            await message.reply(
                f"هیچ سفارش در حال انتظاری برای شما وجود ندارد! "
                f"لطفاً مطمئن شوید که سفارش خود را ثبت کرده‌اید.\n"
                f"وضعیت سفارش‌ها: {all_orders if all_orders else 'هیچ سفارشی یافت نشد'}"
            )
            return
        order = sorted(orders, key=lambda x: x["created_at"], reverse=True)[0]
        order_id, plan_id, is_renewal = (
            order["order_id"],
            order["plan_id"],
            order.get("is_renewal", False),
        )
        plan_type, plan_id = (
            plan_id.split(":") if ":" in plan_id else (plan_id, plan_id)
        )
        logger.debug(
            f"Processing order: {order_id}, plan_id: {plan_id}, is_renewal: {is_renewal}"
        )
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Error checking order for user {user_id}: {e}, response: {response.text if 'response' in locals() else 'No response'}"
        )
        await message.reply(f"خطا در ارتباط با سرور: {str(e)}")
        return

    plan = PLANS.get(plan_type, {}).get(plan_id)
    if not plan:
        logger.error(f"Invalid plan: {plan_type}:{plan_id}")
        await message.reply("پلن نامعتبر است!")
        return

    try:
        file = await bot.get_file(message.photo[-1].file_id)
        receipt_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
    except Exception as e:
        logger.error(f"Failed to get file for order {order_id}: {e}")
        await message.reply("خطا در دریافت فایل رسید!")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="تأیید", callback_data=f"confirm_{order_id}")],
            [InlineKeyboardButton(text="رد", callback_data=f"reject_{order_id}")],
        ]
    )
    receipt_message = await bot.send_photo(
        ADMIN_TELEGRAM_ID,
        photo=message.photo[-1].file_id,
        caption=(
            f"رسید پرداخت برای {'تمدید' if is_renewal else 'سفارش'} {order_id}:\n"
            f"کاربر: {user_id}\n"
            f"پلن: {plan_id} ({plan_type})\n"
            f"حجم: {plan['data_limit'] / 1073741824 if plan['data_limit'] else 'نامحدود'} گیگابایت\n"
            f"مدت: {plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز\n"
            f"مبلغ: {plan['price']} تومان\n"
            f"لینک رسید: {receipt_url}"
        ),
        reply_markup=keyboard,
    )
    logger.info(
        f"Receipt sent to admin for order {order_id}, message_id: {receipt_message.message_id}"
    )

    try:
        response = requests.put(
            f"{DJANGO_API_URL}/orders/{order_id}/",
            json={
                "order_id": order_id,
                "receipt_url": receipt_url,
                "receipt_message_id": receipt_message.message_id,
                "telegram_id": user_id,
                "status": "pending",
            },
            headers={"Content-Type": "application/json"},
            timeout=5,
            verify=True,
        )
        response.raise_for_status()
        logger.info(f"Receipt updated for order {order_id}: {response.json()}")
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Failed to update receipt for order {order_id}: {e}, response: {response.text if 'response' in locals() else 'No response'}"
        )
        await message.reply("خطا در ذخیره رسید! لطفاً دوباره تلاش کنید.")
        return

    await message.reply("رسید شما برای ادمین ارسال شد. منتظر تأیید باشید.")


@dp.callback_query(lambda c: c.data.startswith(("confirm_", "reject_")))
async def process_order_action(callback: CallbackQuery, bot: Bot):
    if not await is_admin(callback.from_user.id):
        await callback.answer("فقط ادمین می‌تواند این عملیات را انجام دهد!")
        return

    action, order_id = callback.data.split("_", 1)
    logger.debug(f"Processing {action} for order {order_id}")

    try:
        response = requests.get(
            f"{DJANGO_API_URL}/orders/{order_id}/", timeout=5, verify=True
        )
        response.raise_for_status()
        order = response.json()
        telegram_id, plan_id, is_renewal = (
            order["telegram_id"],
            order["plan_id"],
            order.get("is_renewal", False),
        )
        plan_type, plan_id = (
            plan_id.split(":") if ":" in plan_id else (plan_id, plan_id)
        )
        logger.info(f"Order {order_id} fetched: {order}")
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Failed to fetch order {order_id}: {e}, response: {response.text if 'response' in locals() else 'No response'}"
        )
        await callback.answer("سفارش یافت نشد!")
        return

    plan = PLANS.get(plan_type, {}).get(plan_id)
    if not plan:
        logger.error(f"Invalid plan: {plan_type}:{plan_id}")
        await callback.answer("پلن نامعتبر است!")
        return

    if action == "confirm":
        try:
            token, username = get_user_data(telegram_id)
            if is_renewal and username:
                user_info = renew_user(
                    username,
                    plan["data_limit"],
                    plan["expire_days"],
                    plan["users"],
                    telegram_id,
                )
                if user_info and "subscription_url" in user_info:
                    save_user_token(
                        telegram_id,
                        user_info["subscription_url"].split("/")[-2],
                        username,
                    )
                    response = requests.put(
                        f"{DJANGO_API_URL}/orders/{order_id}/",
                        json={"status": "confirmed", "telegram_id": telegram_id},
                        headers={"Content-Type": "application/json"},
                        timeout=5,
                        verify=True,
                    )
                    response.raise_for_status()
                    logger.info(f"Order {order_id} confirmed")
                    await bot.send_message(
                        telegram_id,
                        f"تمدید اکانت شما تأیید شد!\n"
                        f"نام کاربری: {username}\n"
                        f"حجم: {plan['data_limit'] / 1073741824 if plan['data_limit'] else 'نامحدود'} گیگابایت\n"
                        f"مدت: {plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز\n"
                        f"لینک اشتراک: {user_info['subscription_url']}\n"
                        f"لطفاً این لینک را ذخیره کنید یا از /getlink برای دریافت مجدد استفاده کنید.",
                    )
                    await callback.message.edit_caption(
                        caption=callback.message.caption + "\n\nوضعیت: تأیید شده"
                    )
                    await callback.answer("تمدید اکانت تأیید شد.")
                else:
                    logger.error(
                        f"Failed to renew user for order {order_id}: user_info={user_info}"
                    )
                    await callback.answer(
                        f"خطا در تمدید اکانت: {user_info.get('error', 'Unknown error')}"
                    )
            else:
                username = f"user_{uuid.uuid4().hex[:8]}"
                user_info = create_user(
                    username,
                    plan["data_limit"],
                    plan["expire_days"],
                    plan["users"],
                    telegram_id,
                )
                if user_info and "subscription_url" in user_info:
                    token = user_info["subscription_url"].split("/")[-2]
                    save_user_token(telegram_id, token, username)
                    response = requests.put(
                        f"{DJANGO_API_URL}/orders/{order_id}/",
                        json={"status": "confirmed", "telegram_id": telegram_id},
                        headers={"Content-Type": "application/json"},
                        timeout=5,
                        verify=True,
                    )
                    response.raise_for_status()
                    logger.info(f"Order {order_id} confirmed")
                    await bot.send_message(
                        telegram_id,
                        f"سفارش شما تأیید شد!\n"
                        f"نام کاربری: {username}\n"
                        f"حجم: {plan['data_limit'] / 1073741824 if plan['data_limit'] else 'نامحدود'} گیگابایت\n"
                        f"مدت: {plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز\n"
                        f"لینک اشتراک: {user_info['subscription_url']}\n"
                        f"لطفاً این لینک را ذخیره کنید یا از /getlink برای دریافت مجدد استفاده کنید.",
                    )
                    await callback.message.edit_caption(
                        caption=callback.message.caption + "\n\nوضعیت: تأیید شده"
                    )
                    await callback.answer("سفارش تأیید شد و اکانت برای کاربر ایجاد شد.")
                else:
                    logger.error(
                        f"Failed to create user for order {order_id}: user_info={user_info}"
                    )
                    await callback.answer(
                        f"خطا در ایجاد اکانت: {user_info.get('error', 'Unknown error')}"
                    )
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to confirm order {order_id}: {e}, response: {response.text if 'response' in locals() else 'No response'}"
            )
            await callback.answer(f"خطا در تأیید سفارش: {str(e)}")
    else:
        try:
            response = requests.put(
                f"{DJANGO_API_URL}/orders/{order_id}/",
                json={"status": "rejected", "telegram_id": telegram_id},
                headers={"Content-Type": "application/json"},
                timeout=5,
                verify=True,
            )
            response.raise_for_status()
            logger.info(f"Order {order_id} rejected")
            await bot.send_message(
                telegram_id,
                f"{'تمدید' if is_renewal else 'سفارش'} {order_id} توسط ادمین رد شد.",
            )
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\nوضعیت: رد شده"
            )
            await callback.answer("سفارش رد شد.")
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to reject order {order_id}: {e}, response: {response.text if 'response' in locals() else 'No response'}"
            )
            await callback.answer(f"خطا در رد سفارش: {str(e)}")


async def main():
    asyncio.create_task(check_pending_orders())
    asyncio.create_task(check_expiring_users())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
