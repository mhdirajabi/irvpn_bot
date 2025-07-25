import uuid

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from config import CARD_HOLDER, CARD_NUMBER, CHANNEL_ID
from keyboards.main_menu import (
    get_channel_join_keyboard,
    get_main_menu,
    get_main_menu_inline,
)
from keyboards.renew_menu import get_renew_menu, get_renew_plan_menu
from services.check_channel_membership import check_channel_membership
from services.order_service import save_order
from services.user_service import get_user_data
from utils.logger import logger
from utils.plans import PLANS

router = Router()


@router.message(Command("renew"))
@router.message(F.text == "🔄 تمدید اکانت")
async def renew_command(message: Message, bot: Bot):
    user_id = message.from_user.id
    if not await check_channel_membership(bot, user_id):
        await message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
        )
        return
    token, username = await get_user_data(user_id)
    if not username:
        await message.reply(
            "⚠️ *لطفاً اول کد اشتراک رو با /settoken وارد کنید.*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return
    await message.reply(
        "*لطفاً نوع اکانت برای تمدید رو انتخاب کن:*",
        parse_mode="Markdown",
        reply_markup=get_renew_menu(),
    )


@router.callback_query(lambda c: c.data == "main_renew")
async def main_renew(callback: CallbackQuery, bot: Bot):
    logger.debug(f"Received callback: main_renew from user {callback.from_user.id}")
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logger.warning(f"Failed to delete message in main_renew: {str(e)}")
    message = callback.message
    message.from_user = callback.from_user
    await renew_command(message, bot)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("renew_"))
async def process_renew_type(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if not await check_channel_membership(bot, user_id):
        await callback.message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}", parse_mode="Markdown"
        )
        return
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logger.warning(f"Failed to delete message in process_renew_type: {str(e)}")
    account_type = callback.data.split("_")[1]
    plans = PLANS.get(account_type, {})
    if not plans:
        await callback.message.answer(
            "❌ *نوع اکانت نامعتبر است!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu_inline(),
        )
        return
    await callback.message.answer(
        f"*لطفاً پلن {account_type} برای تمدید رو انتخاب کن:*",
        parse_mode="Markdown",
        reply_markup=get_renew_plan_menu(account_type, plans),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("renewselect_"))
async def process_renew_plan_selection(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    if not await check_channel_membership(bot, user_id):
        await callback.message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}", parse_mode="Markdown"
        )
        return
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logger.warning(
            f"Failed to delete message in process_renew_plan_selection: {str(e)}"
        )
    _, account_type, plan_id = callback.data.split("_")
    plan = PLANS.get(account_type, {}).get(plan_id)
    if not plan:
        await callback.message.answer(
            "❌ *پلن نامعتبر است!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu_inline(),
        )
        return
    order_id = str(uuid.uuid4())
    await save_order(
        user_id, order_id, plan_id, account_type, plan["price"], is_renewal=True
    )
    await callback.message.answer(
        f"شما پلن *{plan_id}* ({account_type}) برای تمدید انتخاب کردی:\n"
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
