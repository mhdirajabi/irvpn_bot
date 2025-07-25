import uuid

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from config import CARD_HOLDER, CARD_NUMBER, CHANNEL_ID
from keyboards.buy_menu import get_buy_menu, get_plan_menu
from keyboards.main_menu import (
    get_channel_join_keyboard,
    get_main_menu,
    get_main_menu_inline,
)
from services.check_channel_membership import check_channel_membership
from services.order_service import save_order
from services.user_service import create_user, save_user_token
from utils.logger import logger
from utils.plans import PLANS

router = Router()


@router.message(Command("buy"))
@router.message(F.text == "🛒 خرید اکانت")
async def buy_command(message: Message, bot: Bot):
    if message.from_user is None:
        await message.reply(
            "❌ *خطا: اطلاعات کاربر یافت نشد!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu_inline(),
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
    await message.reply(
        "*لطفاً نوع اکانت را انتخاب کنید:*",
        parse_mode="Markdown",
        reply_markup=get_buy_menu(),
    )


@router.callback_query(lambda c: c.data == "main_buy")
async def main_buy(callback: CallbackQuery, bot: Bot):
    logger.debug(f"Received callback: main_buy from user {callback.from_user.id}")
    try:
        try:
            if callback.message is not None:
                await bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    reply_markup=None,
                )
        except TelegramBadRequest as e:
            logger.warning(f"Failed to edit reply markup in main_buy: {str(e)}")
    except TelegramBadRequest as e:
        logger.warning(f"Failed to delete message in main_buy: {str(e)}")
    message = callback.message
    await buy_command(message, bot)
    await callback.answer()


@router.callback_query(lambda c: c.data == "buy_back")
async def buy_back(callback: CallbackQuery, bot: Bot):
    logger.debug(f"Received callback: buy_back from user {callback.from_user.id}")

    try:
        if callback.message is not None:
            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=None,
            )
    except TelegramBadRequest as e:
        logger.warning(f"Failed to edit reply markup in buy_back: {str(e)}")
    if callback.message is not None:
        await callback.message.answer(
            "*لطفاً نوع اکانت را انتخاب کنید:*",
            parse_mode="Markdown",
            reply_markup=get_buy_menu(),
        )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("buy_"))
async def process_account_type(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if not await check_channel_membership(bot, user_id):
        if callback.message is not None:
            await callback.message.reply(
                f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
                parse_mode="Markdown",
            )
        return
    try:
        if callback.message is not None:
            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=None,
            )
    except TelegramBadRequest as e:
        logger.warning(f"Failed to edit reply markup in process_account_type: {str(e)}")
    if not callback.data:
        if callback.message is not None:
            await callback.message.answer(
                "❌ *خطا: داده‌ای برای پردازش وجود ندارد!*",
                parse_mode="Markdown",
                reply_markup=get_main_menu_inline(),
            )
            return
    else:
        account_type = callback.data.split("_")[1]
        plans = PLANS.get(account_type, {})
        if not plans:
            if callback.message is not None:
                await callback.message.answer(
                    "❌ *نوع اکانت نامعتبر است!*",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_inline(),
                )
            return
        if callback.message is not None:
            await callback.message.answer(
                f"*لطفاً پلن {account_type} مورد نظر را انتخاب کنید:*",
                parse_mode="Markdown",
                reply_markup=get_plan_menu(account_type, plans),
            )
        await callback.answer()


@router.callback_query(lambda c: c.data.startswith("select_"))
async def process_plan_selection(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if not await check_channel_membership(bot, user_id):
        if callback.message is not None:
            await callback.message.reply(
                f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
                parse_mode="Markdown",
            )
        return
    try:
        if callback.message is not None:
            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=None,
            )
    except TelegramBadRequest as e:
        logger.warning(
            f"Failed to edit reply markup in process_plan_selection: {str(e)}"
        )
    if not callback.data:
        if callback.message is not None:
            await callback.message.answer(
                "❌ *خطا: داده‌ای برای پردازش وجود ندارد!*",
                parse_mode="Markdown",
                reply_markup=get_main_menu_inline(),
            )
            return
    else:
        _, account_type, plan_id = callback.data.split("_")
        plan = PLANS.get(account_type, {}).get(plan_id)
        if not plan:
            if callback.message is not None:
                await callback.message.answer(
                    "❌ *پلن نامعتبر است!*",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_inline(),
                )
            return
        if plan["price"] == 0:
            username = f"user_{uuid.uuid4().hex[:8]}"
            user_info = await create_user(
                username,
                plan["data_limit"],
                plan["expire_days"],
                plan["users"],
                user_id,
            )
            if user_info:
                token = user_info["subscription_url"].split("/")[-2]
                await save_user_token(user_id, token, username)
                if callback.message is not None:
                    await callback.message.answer(
                        f"اکانت تست شما ایجاد شد! 🎉\n"
                        f"👤 *نام کاربری*: {username}\n"
                        f"📈 *حجم*: {plan['data_limit'] / 1073741824 if plan['data_limit'] else '♾️ نامحدود'} گیگابایت\n"
                        f"⏳ *مدت*: {plan['expire_days']} روز\n"
                        f"🔗 *لینک اشتراک*: {user_info['subscription_url']}\n"
                        f"لطفاً این لینک رو ذخیره کن یا از /getlink برای دریافت مجدد استفاده کن.",
                        parse_mode="Markdown",
                        reply_markup=get_main_menu(),
                    )
            else:
                if callback.message is not None:
                    await callback.message.answer(
                        "❌ *خطا در ایجاد اکانت تست!*",
                        parse_mode="Markdown",
                        reply_markup=get_main_menu(),
                    )
            await callback.answer()
            return
        order_id = str(uuid.uuid4())
        await save_order(user_id, order_id, plan_id, account_type, plan["price"])
        if callback.message is not None:
            await callback.message.answer(
                f"شما پلن *{plan_id}* ({account_type}) رو انتخاب کردی:\n"
                f"📈 *حجم*: {plan['data_limit'] / 1073741824 if plan['data_limit'] else '♾️ نامحدود'} گیگابایت\n"
                f"⏳ *مدت*: {plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز\n"
                f"💸 *مبلغ*: {plan['price']} تومان\n\n"
                f"لطفاً مبلغ رو به شماره کارت زیر واریز کن و رسید رو ظرف 30 دقیقه بفرست:\n"
                f"💳 *شماره کارت*: `{CARD_NUMBER}` (به نام {CARD_HOLDER})\n\n"
                f"برای ارسال رسید، کافیه عکس رسید رو همینجا بفرستی.",
                parse_mode="Markdown",
                reply_markup=get_main_menu(),
            )
        await callback.answer()
