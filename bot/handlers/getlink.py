from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from config import CHANNEL_ID, API_BASE_URL
from keyboards.main_menu import get_channel_join_keyboard, get_main_menu
from services.api_client import APIClient
from services.check_channel_membership import check_channel_membership
from services.user_service import get_user_by_telegram_id
from utils.logger import logger

router = Router()


@router.message(Command("getlink"))
@router.message(F.text == "🔗 دریافت لینک")
async def getlink_command(message: Message, bot: Bot):
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
    try:
        user = await get_user_by_telegram_id(user_id)
        if not user or not user.get("subscription_url"):
            await message.answer(
                "⚠️ *لینکی برای اکانت شما پیدا نشد!*",
                parse_mode="Markdown",
                reply_markup=get_main_menu(),
            )
            return
        await message.answer(
            f"*لینک اشتراک شما:* 🔗\n`{API_BASE_URL}{user['subscription_url']}`",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
    except Exception as e:
        logger.error(f"Failed to fetch link for telegram_id={user_id}: {e}")
        await message.answer(
            "❌ *خطا در دریافت لینک اشتراک!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )


@router.callback_query(lambda c: c.data == "main_getlink")
async def main_getlink(callback: CallbackQuery, bot: Bot):
    logger.debug(f"Received callback: main_getlink from user {callback.from_user.id}")

    if isinstance(callback.message, Message):
        try:
            await callback.message.delete()
        except TelegramBadRequest as e:
            logger.warning(f"Failed to delete message in main_getlink: {str(e)}")
    else:
        logger.warning(
            "callback.message is not deletable (InaccessibleMessage or None)"
        )

    message = callback.message
    if isinstance(message, Message):
        message.from_user = callback.from_user

    await getlink_command(message, bot)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("getlink_"))
async def process_client_type(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if not await check_channel_membership(bot, user_id):
        if callback.message:
            await callback.message.reply(
                f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
                parse_mode="Markdown",
            )
        return
    if isinstance(callback.message, Message):
        try:
            await callback.message.delete()
        except TelegramBadRequest as e:
            logger.warning(f"Failed to delete message in process_client_type: {str(e)}")
    else:
        logger.warning(
            "callback.message is not deletable (InaccessibleMessage or None)"
        )
    if callback.data:
        client_type, token = callback.data.split("_")[1:3]
        try:
            response = await APIClient.get(f"/sub/{token}/{client_type}")
            if callback.message:
                await callback.message.answer(
                    f"*لینک اشتراک ({client_type}):*\n`{response}`",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu(),
                )
        except Exception as e:
            logger.error(f"Failed to fetch client link for token={token}: {e}")
            if callback.message:
                await callback.message.answer(
                    "❌ *خطا در دریافت لینک اشتراک!*",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu(),
                )
        await callback.answer()
