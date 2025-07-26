from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from config import CHANNEL_ID
from keyboards.main_menu import get_channel_join_keyboard, get_main_menu
from services.check_channel_membership import check_channel_membership
from services.user_service import get_user_by_telegram_id
from utils.formatters import format_data_limit, format_expire_date
from utils.logger import logger

router = Router()


@router.message(Command("status"))
@router.message(F.text == "📊 وضعیت اکانت")
async def status_command(message: Message, bot: Bot):
    user_id = message.from_user.id
    if not await check_channel_membership(bot, user_id):
        await message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
        )
        return
    try:
        user = await get_user_by_telegram_id(user_id)
        if not user:
            await message.answer(
                "⚠️ *هیچ اکانتی برای شما پیدا نشد!*",
                parse_mode="Markdown",
                reply_markup=get_main_menu(),
            )
            return
        await message.answer(
            f"*وضعیت اکانت شما:* 📋\n"
            f"👤 *نام کاربری*: {user['username']}\n"
            f"📈 *حجم*: {format_data_limit(user['data_limit'])}\n"
            f"⏳ *انقضا*: {format_expire_date(user['expire'])}\n"
            f"✅ *وضعیت*: {user['status']}",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
    except Exception as e:
        logger.error(f"Failed to fetch user status for telegram_id={user_id}: {e}")
        await message.answer(
            "❌ *خطا در دریافت اطلاعات اکانت!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )


@router.callback_query(lambda c: c.data == "main_status")
async def main_status(callback: CallbackQuery, bot: Bot):
    logger.debug(f"Received callback: main_status from user {callback.from_user.id}")
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logger.warning(f"Failed to delete message in main_status: {str(e)}")
    user_id = callback.from_user.id
    if not await check_channel_membership(bot, user_id):
        await callback.message.answer(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
        )
        await callback.answer()
        return
    try:
        user = await get_user_by_telegram_id(user_id)
        if not user:
            await callback.message.answer(
                "⚠️ *هیچ اکانتی برای شما پیدا نشد!*",
                parse_mode="Markdown",
                reply_markup=get_main_menu(),
            )
            await callback.answer()
            return
        await callback.message.answer(
            f"*وضعیت اکانت شما:* 📋\n"
            f"👤 *نام کاربری*: {user['username']}\n"
            f"📈 *حجم*: {format_data_limit(user['data_limit'])}\n"
            f"⏳ *انقضا*: {format_expire_date(user['expire'])}\n"
            f"✅ *وضعیت*: {user['status']}",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
    except Exception as e:
        logger.error(f"Failed to fetch user status for telegram_id={user_id}: {e}")
        await callback.message.answer(
            "❌ *خطا در دریافت اطلاعات اکانت!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
    await callback.answer()
