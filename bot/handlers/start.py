from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from config import ADMIN_TELEGRAM_ID, CHANNEL_ID
from keyboards.main_menu import (
    get_channel_join_keyboard,
    get_main_menu,
    get_main_menu_inline,
)
from services.check_channel_membership import check_channel_membership
from utils.logger import logger

router = Router()


async def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_TELEGRAM_ID


@router.message(Command("start"))
async def start_command(message: Message, bot: Bot):
    if message.from_user is None:
        await message.reply("خطا: کاربر شناسایی نشد. لطفاً دوباره تلاش کنید.")
        return
    user_id = message.from_user.id
    if not await check_channel_membership(bot, user_id):
        await message.reply(
            "🎉 *به ربات IRVPN خوش اومدی!* 😊\n"
            "برای استفاده از خدمات ما، لطفاً ابتدا توی کانالممون عضو شو:\n"
            f"👉 *{CHANNEL_ID}*\n"
            "بعد از عضویت، دکمه زیر رو بزن تا ادامه بدیم!",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
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


@router.callback_query(lambda c: c.data == "check_membership")
async def check_membership(callback: CallbackQuery, bot: Bot):
    logger.debug(
        f"Received callback: check_membership from user {callback.from_user.id}"
    )
    if isinstance(callback.message, Message):
        try:
            await bot.delete_message(
                chat_id=callback.message.chat.id, message_id=callback.message.message_id
            )
        except TelegramBadRequest as e:
            logger.warning(f"Failed to delete message in check_membership: {str(e)}")
    else:
        logger.warning("Callback message is not of type Message, skipping deletion.")

    user_id = callback.from_user.id
    if await check_channel_membership(bot, user_id):
        is_admin_user = await is_admin(user_id)
        reply = (
            "*خوش اومدی!* 🎉\n"
            "حالا می‌تونی از خدمات ربات استفاده کنی. یه گزینه رو انتخاب کن:\n\n"
            f"{'*دستورات ادمین*:\n/adduser - ایجاد کاربر جدید\n/servers - مدیریت سرورها\n' if is_admin_user else ''}"
            "📊 *وضعیت اکانت*: بررسی وضعیت اشتراک\n"
            "🛒 *خرید اکانت*: خرید اکانت جدید\n"
            "🔄 *تمدید اکانت*: تمدید اشتراک موجود\n"
            "🔗 *دریافت لینک*: دریافت لینک اشتراک"
        )
        if callback.message is not None:
            await callback.message.answer(
                reply, parse_mode="Markdown", reply_markup=get_main_menu()
            )
        if callback.message is not None:
            await callback.message.answer(
                "⚠️ *هنوز توی کانال ما عضو نشدی!* 😔\n"
                f"لطفاً توی {CHANNEL_ID} عضو شو و دوباره امتحان کن!",
                parse_mode="Markdown",
                reply_markup=get_channel_join_keyboard(),
            )
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, bot: Bot):
    logger.debug(f"Received callback: back_to_main from user {callback.from_user.id}")
    try:
        if callback.message is not None:
            await bot.delete_message(
                chat_id=callback.message.chat.id, message_id=callback.message.message_id
            )
    except TelegramBadRequest as e:
        logger.warning(f"Failed to delete message in back_to_main: {str(e)}")
    try:
        if callback.message is not None:
            await callback.message.answer(
                "*به منوی اصلی خوش اومدی!* 😊\nلطفاً یک گزینه انتخاب کن:",
                parse_mode="Markdown",
                reply_markup=get_main_menu_inline(),
            )
    except Exception:
        if callback.message is not None:
            await callback.message.answer(
                "❌ *خطایی رخ داد! لطفاً دوباره امتحان کنید.*",
                parse_mode="Markdown",
                reply_markup=get_main_menu(),
            )
    await callback.answer()
