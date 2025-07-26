from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from config import ADMIN_TELEGRAM_ID, API_BASE_URL, CHANNEL_ID
from keyboards.main_menu import get_channel_join_keyboard, get_main_menu
from services.api_client import APIClient
from services.check_channel_membership import check_channel_membership
from services.user_service import create_user, save_user_token
from utils.logger import logger
from utils.marzban import get_jwt_token


router = Router()


async def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_TELEGRAM_ID


@router.message(Command("adduser"))
async def adduser_command(message: Message, bot: Bot):
    if not message.from_user:
        await message.reply(
            "❌ *خطا: کاربر نامشخص است!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return
    user_id = message.from_user.id
    if not await check_channel_membership(bot, user_id):
        await message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
        )
        return
    if not await is_admin(user_id):
        await message.reply(
            "❌ *این دستور فقط برای ادمین‌ها قابل استفاده است!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return
    if not message.text:
        await message.reply(
            "❌ *خطا: متن پیام یافت نشد!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return
    args = message.text.split(maxsplit=4)
    if len(args) < 5:
        await message.reply(
            "لطفاً اطلاعات کاربر رو وارد کنید:\n"
            "/adduser <username> <data_limit_in_GB> <expire_days> <users>\n"
            "مثال: /adduser user123 10 30 unlimited",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return
    username, data_limit, expire_days, users = args[1:5]
    try:
        data_limit = float(data_limit) * 1073741824 if data_limit != "0" else 0
        user_info = await create_user(
            user_id, username, int(data_limit), int(expire_days), users
        )
        if user_info:
            token = user_info["subscription_url"].split("/")[-2]
            await save_user_token(user_id, token, username)
            await message.reply(
                f"کاربر *{username}* با موفقیت ایجاد شد! 🎉\n" f"🔗 *Token*: `{token}`",
                parse_mode="Markdown",
                reply_markup=get_main_menu(),
            )
        else:
            await message.reply(
                "❌ *خطا در ایجاد کاربر!*",
                parse_mode="Markdown",
                reply_markup=get_main_menu(),
            )
    except Exception as e:
        logger.error(f"Failed to add user {username}: {e}")
        await message.reply(
            f"❌ *خطا*: {str(e)}", parse_mode="Markdown", reply_markup=get_main_menu()
        )


@router.message(Command("servers"))
async def servers_command(message: Message, bot: Bot):
    if not message.from_user:
        await message.reply(
            "❌ *خطا: کاربر نامشخص است!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return
    user_id = message.from_user.id
    if not await check_channel_membership(bot, user_id):
        await message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
        )
        return
    if not await is_admin(user_id):
        await message.reply(
            "❌ *این دستور فقط برای ادمین‌ها قابل استفاده است!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return
    try:
        headers = {"Authorization": f"Bearer {get_jwt_token()}"}
        nodes = await APIClient.get(
            "/api/nodes", headers=headers, base_url=API_BASE_URL
        )
        reply = "*لیست سرورها:* 🗄️\n\n"
        for node in nodes:
            reply += f"🖥️ *ID*: {node['id']}, *نام*: {node['name']}, *وضعیت*: {node['status']}\n"
        await message.reply(reply, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Failed to fetch servers: {e}")
        await message.reply(
            f"❌ *خطا در دریافت لیست سرورها*: {str(e)}",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
