import uuid

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from config import CARD_HOLDER, CARD_NUMBER, CHANNEL_ID
from keyboards.buy_menu import get_buy_menu, get_plan_menu
from keyboards.main_menu import (
    get_admin_menu,
    get_admin_menu_inline,
    get_channel_join_keyboard,
    get_main_menu,
    get_main_menu_inline,
)
from services.check_channel_membership import check_channel_membership
from services.order_service import (
    save_order,
)
from utils.logger import logger
from utils.plans import get_plan_by_id

from .admin import is_admin

router = Router()


@router.message(Command("buy"))
@router.message(F.text == "🛒 خرید اکانت")
async def buy_command(message: Message, bot: Bot):
    if not message.from_user:
        await message.reply(
            "❌ *خطا: کاربر نامشخص است!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return
    user_id = message.from_user.id
    logger.info(f"Buy command received from user {user_id}")
    if not await check_channel_membership(bot, user_id):
        await message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
        )
        return
    await message.answer(
        "*لطفاً نوع اکانت رو انتخاب کن:*",
        parse_mode="Markdown",
        reply_markup=get_buy_menu(),
    )


@router.callback_query(lambda c: c.data == "main_buy")
async def main_buy(callback: CallbackQuery, bot: Bot):
    logger.debug(f"Received callback: main_buy from user {callback.from_user.id}")

    if isinstance(callback.message, Message):
        try:
            await callback.message.delete()
        except TelegramBadRequest as e:
            logger.warning(f"Failed to delete message in main_buy: {e}")
    else:
        logger.warning(
            "callback.message is not deletable (InaccessibleMessage or None)"
        )

    user_id = callback.from_user.id

    if not await check_channel_membership(bot, user_id):
        if callback.message:
            await callback.message.answer(
                f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
                parse_mode="Markdown",
                reply_markup=get_channel_join_keyboard(),
            )
        await callback.answer()
        return
    if callback.message:
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
        if callback.message:
            await callback.message.answer(
                f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
                parse_mode="Markdown",
                reply_markup=get_channel_join_keyboard(),
            )
        await callback.answer()
        return
    if isinstance(callback.message, Message):
        try:
            await callback.message.delete()
            if callback.data:
                category = callback.data.split("_")[1]
                if category == "volume":
                    plan_dsc = "**حجمی**"
                elif category == "unlimited":
                    plan_dsc = "**نامحدود**"
                elif category == "test":
                    plan_dsc = "**تست**"
                else:
                    plan_dsc = "**نامشخص**"
                logger.debug(f"Selected category: {category}")
                if category == "back":
                    is_admin_user = await is_admin(user_id)
                    (
                        await callback.message.answer(
                            "*به منوی اصلی خوش اومدی!* 😊\nلطفاً یک گزینه انتخاب کن:",
                            parse_mode="Markdown",
                            reply_markup=get_main_menu_inline(),
                        )
                        if not is_admin_user
                        else await callback.message.answer(
                            "*به منوی اصلی خوش اومدی!* 😊\nلطفاً یک گزینه انتخاب کن:",
                            parse_mode="Markdown",
                            reply_markup=get_admin_menu_inline(),
                        )
                    )
                else:
                    await callback.message.answer(
                        f"*لطفاً پلن {plan_dsc} رو انتخاب کن:*",
                        parse_mode="Markdown",
                        reply_markup=get_plan_menu(category),
                    )
        except TelegramBadRequest as e:
            logger.warning(f"Failed to delete message in process_buy_type: {e}")
    else:
        logger.warning(
            "callback.message is not deletable (InaccessibleMessage or None)"
        )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("select_"))
async def process_plan_selection(callback: CallbackQuery, bot: Bot):
    logger.info(
        f"Received select callback: {callback.data} from user {callback.from_user.id}"
    )
    user_id = callback.from_user.id
    is_admin_user = await is_admin(user_id)
    if not await check_channel_membership(bot, user_id):
        if callback.message:
            await callback.message.answer(
                f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
                parse_mode="Markdown",
                reply_markup=get_channel_join_keyboard(),
            )
        await callback.answer()
        return
    if isinstance(callback.message, Message):
        try:
            await callback.message.delete()
        except TelegramBadRequest as e:
            logger.warning(f"Failed to delete message in process_plan_selection: {e}")
    else:
        logger.warning(
            "callback.message is not deletable (InaccessibleMessage or None)"
        )
    if callback.data:
        flag = callback.data.split("_")[1]
        if flag == "back":
            if callback.message:
                await callback.message.answer(
                    "*لطفاً نوع اکانت رو انتخاب کن:*",
                    parse_mode="Markdown",
                    reply_markup=get_buy_menu(),
                )
        else:
            plan_id = callback.data.replace("select_", "")
            logger.debug(f"Selected plan_id: {plan_id}")
            plan = get_plan_by_id(plan_id)
            if not plan:
                logger.error(f"Invalid plan_id: {plan_id}")
                if callback.message:
                    (
                        await callback.message.answer(
                            "❌ *پلن نامعتبر است!*",
                            parse_mode="Markdown",
                            reply_markup=get_main_menu(),
                        )
                        if not is_admin_user
                        else await callback.message.answer(
                            "❌ *پلن نامعتبر است!*",
                            parse_mode="Markdown",
                            reply_markup=get_admin_menu(),
                        )
                    )
                await callback.answer()
                return
            order_id = str(uuid.uuid4())
            try:
                await save_order(user_id, order_id, plan_id, int(plan["price"]))
                if callback.message:
                    (
                        await callback.message.answer(
                            f"شما پلن *{plan['name']}* رو انتخاب کردی:\n"
                            f"📈 *حجم*: {int(plan['data_limit']) / 1073741824 if plan['data_limit'] else '♾️ نامحدود'} گیگابایت\n"
                            f"⏳ *مدت*: {plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز\n"
                            f"💸 *مبلغ*: {plan['price']} تومان\n\n"
                            f"لطفاً مبلغ رو به شماره کارت زیر واریز کن و رسید رو ظرف 30 دقیقه بفرست:\n"
                            f"💳 *شماره کارت*: `{CARD_NUMBER}` (به نام {CARD_HOLDER})\n\n"
                            f"برای ارسال رسید، کافیه عکس رسید رو همینجا بفرستی.",
                            parse_mode="Markdown",
                            reply_markup=get_main_menu(),
                        )
                        if not is_admin_user
                        else await callback.message.answer(
                            f"شما پلن *{plan['name']}* رو انتخاب کردی:\n"
                            f"📈 *حجم*: {int(plan['data_limit']) / 1073741824 if plan['data_limit'] else '♾️ نامحدود'} گیگابایت\n"
                            f"⏳ *مدت*: {plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز\n"
                            f"💸 *مبلغ*: {plan['price']} تومان\n\n"
                            f"لطفاً مبلغ رو به شماره کارت زیر واریز کن و رسید رو ظرف 30 دقیقه بفرست:\n"
                            f"💳 *شماره کارت*: `{CARD_NUMBER}` (به نام {CARD_HOLDER})\n\n"
                            f"برای ارسال رسید، کافیه عکس رسید رو همینجا بفرستی.",
                            parse_mode="Markdown",
                            reply_markup=get_admin_menu(),
                        )
                    )
            except Exception as e:
                logger.error(f"Failed to save order for user {user_id}: {e}")
                if callback.message:
                    (
                        await callback.message.answer(
                            "❌ *خطا در ثبت سفارش! لطفاً دوباره امتحان کنید.*",
                            parse_mode="Markdown",
                            reply_markup=get_main_menu(),
                        )
                        if not is_admin_user
                        else await callback.message.answer(
                            "❌ *خطا در ثبت سفارش! لطفاً دوباره امتحان کنید.*",
                            parse_mode="Markdown",
                            reply_markup=get_admin_menu(),
                        )
                    )
        await callback.answer()
