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
)
from services.check_channel_membership import check_channel_membership
from services.order_service import (
    save_order,
)
from utils.logger import logger
from utils.plans import get_plan_by_id

router = Router()


@router.message(Command("buy"))
@router.message(F.text == "🛒 خرید اکانت")
async def buy_command(message: Message, bot: Bot):
    user_id = message.from_user.id
    logger.info(f"Buy command received from user {user_id}")
    if not await check_channel_membership(bot, user_id):
        await message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
        )
        return
    await message.reply(
        "*لطفاً نوع اکانت رو انتخاب کن:*",
        parse_mode="Markdown",
        reply_markup=get_buy_menu(),
    )


@router.callback_query(lambda c: c.data == "main_buy")
async def main_buy(callback: CallbackQuery, bot: Bot):
    logger.debug(f"Received callback: main_buy from user {callback.from_user.id}")
    try:
        await callback.message.delete()
    except TelegramBadRequest as e:
        logger.warning(f"Failed to delete message in main_buy: {e}")
    user_id = callback.from_user.id
    if not await check_channel_membership(bot, user_id):
        await callback.message.answer(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
        )
        await callback.answer()
        return
    await callback.message.answer(
        "*لطفاً نوع اکانت رو انتخاب کن:*",
        parse_mode="Markdown",
        reply_markup=get_buy_menu(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("buy_"))
async def process_buy_type(callback: CallbackQuery, bot: Bot):
    logger.info(
        f"Received buy callback: {callback.data} from user {callback.from_user.id}"
    )
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
        await callback.message.delete()
    except TelegramBadRequest as e:
        logger.warning(f"Failed to delete message in process_buy_type: {e}")
    category = callback.data.split("_")[1]
    logger.debug(f"Selected category: {category}")
    if category == "back":
        await callback.message.answer(
            "*لطفاً نوع اکانت رو انتخاب کن:*",
            parse_mode="Markdown",
            reply_markup=get_buy_menu(),
        )
    else:
        await callback.message.answer(
            f"*لطفاً پلن {category} رو انتخاب کن:*",
            parse_mode="Markdown",
            reply_markup=get_plan_menu(category),
        )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("select_"))
async def process_plan_selection(callback: CallbackQuery, bot: Bot):
    logger.info(
        f"Received select callback: {callback.data} from user {callback.from_user.id}"
    )
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
        await callback.message.delete()
    except TelegramBadRequest as e:
        logger.warning(f"Failed to delete message in process_plan_selection: {e}")
    plan_id = callback.data.replace("select_", "")
    logger.debug(f"Selected plan_id: {plan_id}")
    plan = get_plan_by_id(plan_id)
    if not plan:
        logger.error(f"Invalid plan_id: {plan_id}")
        await callback.message.answer(
            "❌ *پلن نامعتبر است!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        await callback.answer()
        return
    order_id = str(uuid.uuid4())
    try:
        await save_order(user_id, order_id, plan_id, plan["price"])
        await callback.message.answer(
            f"شما پلن *{plan['name']}* رو انتخاب کردی:\n"
            f"📈 *حجم*: {plan['data_limit'] / 1073741824 if plan['data_limit'] else '♾️ نامحدود'} گیگابایت\n"
            f"⏳ *مدت*: {plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز\n"
            f"💸 *مبلغ*: {plan['price']} تومان\n\n"
            f"لطفاً مبلغ رو به شماره کارت زیر واریز کن و رسید رو ظرف 30 دقیقه بفرست:\n"
            f"💳 *شماره کارت*: `{CARD_NUMBER}` (به نام {CARD_HOLDER})\n\n"
            f"برای ارسال رسید، کافیه عکس رسید رو همینجا بفرستی.",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
    except Exception as e:
        logger.error(f"Failed to save order for user {user_id}: {e}")
        await callback.message.answer(
            "❌ *خطا در ثبت سفارش! لطفاً دوباره امتحان کنید.*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
    await callback.answer()
