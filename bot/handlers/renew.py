import uuid

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from config import CARD_HOLDER, CARD_NUMBER, CHANNEL_ID
from keyboards.main_menu import get_channel_join_keyboard, get_main_menu
from keyboards.renew_menu import get_renew_menu, get_renew_plan_menu
from services.check_channel_membership import check_channel_membership
from services.order_service import save_order
from services.user_service import get_user_by_telegram_id
from utils.logger import logger
from utils.plans import get_plan_by_id

router = Router()


@router.message(Command("renew"))
@router.message(F.text == "🔄 تمدید اکانت")
async def renew_command(message: Message, bot: Bot):
    user_id = str(message.from_user.id)
    logger.info(f"Renew command received from user {user_id}")
    if not await check_channel_membership(bot, user_id):
        await message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
        )
        return
    user = await get_user_by_telegram_id(user_id)
    if not user:
        await message.reply(
            "⚠️ *هیچ اکانتی برای شما پیدا نشد!*",
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
        logger.warning(f"Failed to delete message in main_renew: {e}")
    user_id = str(callback.from_user.id)
    if not await check_channel_membership(bot, user_id):
        await callback.message.answer(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
        )
        await callback.answer()
        return
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
        "*لطفاً نوع اکانت برای تمدید رو انتخاب کن:*",
        parse_mode="Markdown",
        reply_markup=get_renew_menu(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("renew_"))
async def process_renew_type(callback: CallbackQuery, bot: Bot):
    logger.info(
        f"Received renew callback: {callback.data} from user {callback.from_user.id}"
    )
    user_id = str(callback.from_user.id)
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
        logger.warning(f"Failed to delete message in process_renew_type: {e}")
    category = callback.data.split("_")[1]
    logger.debug(f"Selected category: {category}")
    await callback.message.answer(
        f"*لطفاً پلن {category} برای تمدید رو انتخاب کن:*",
        parse_mode="Markdown",
        reply_markup=get_renew_plan_menu(category),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("renewselect_"))
async def process_renew_plan_selection(callback: CallbackQuery, bot: Bot):
    logger.info(
        f"Received renewselect callback: {callback.data} from user {callback.from_user.id}"
    )
    user_id = str(callback.from_user.id)
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
        logger.warning(f"Failed to delete message in process_renew_plan_selection: {e}")
    plan_id = callback.data.replace("renewselect_", "")
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
        await save_order(user_id, order_id, plan_id, plan["price"], is_renewal=True)
        await callback.message.answer(
            f"شما پلن *{plan['name']}* برای تمدید انتخاب کردی:\n"
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
        logger.error(f"Failed to save renewal order for user {user_id}: {e}")
        await callback.message.answer(
            "❌ *خطا در ثبت سفارش تمدید! لطفاً دوباره امتحان کنید.*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
    await callback.answer()
