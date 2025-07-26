import uuid

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message
from config import ADMIN_TELEGRAM_ID, BOT_TOKEN, CHANNEL_ID
from handlers.admin import is_admin
from keyboards.main_menu import get_channel_join_keyboard, get_main_menu
from keyboards.receipt_menu import get_receipt_admin_menu
from services.check_channel_membership import check_channel_membership
from services.order_service import (
    get_order,
    get_orders,
    get_pending_orders,
    update_order,
)
from services.user_service import (
    create_user,
    get_user_by_telegram_id,
    renew_user,
    save_user_token,
)
from utils.logger import logger
from utils.plans import get_plan_by_id

router = Router()


@router.message(F.photo)
async def handle_receipt(message: Message, bot: Bot):
    if not message.from_user:
        await message.reply(
            "❌ *خطا: کاربر نامشخص است!*",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )
        return
    user_id = message.from_user.id

    logger.info(f"Handling receipt for user: {user_id}")

    if not await check_channel_membership(bot, user_id):
        logger.warning(f"User {user_id} not in channel {CHANNEL_ID}")
        await message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_join_keyboard(),
        )
        return

    try:
        orders = await get_pending_orders(user_id)
        logger.info(f"Orders fetched for user {user_id}: {orders}")
        if not orders:
            logger.warning(f"No pending orders found for user {user_id}")
            all_orders = await get_orders(user_id)
            await message.reply(
                f"⚠️ *هیچ سفارش در حال انتظاری برای شما وجود ندارد!* \n"
                f"لطفاً مطمئن شوید که سفارش خود را ثبت کرده‌اید.\n"
                f"وضعیت سفارش‌ها: {all_orders if all_orders else 'هیچ سفارشی یافت نشد'}",
                parse_mode="markdown",
                reply_markup=get_main_menu(),
            )
            return
        order = sorted(orders, key=lambda x: x["created_at"], reverse=True)[0]
        order_id, plan_id, is_renewal = (
            order["order_id"],
            order["plan_id"],
            order.get("is_renewal", False),
        )
        plan = get_plan_by_id(plan_id)
        if not plan:
            logger.error(f"Invalid plan: {plan_id}")
            await message.reply("❌ *پلن نامعتبر است!*", parse_mode="Markdown")
            return
        logger.debug(
            f"Processing order: {order_id}, plan_id: {plan_id}, is_renewal: {is_renewal}"
        )
    except Exception as e:
        logger.error(f"Error checking order for user {user_id}: {e}")
        await message.reply(
            f"❌ *خطا در ارتباط با سرور*: {str(e)}", parse_mode="markdown"
        )
        return

    try:
        if message.photo:
            file = await bot.get_file(message.photo[-1].file_id)
            receipt_url = (
                f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
            )
            caption = (
                f"رسید پرداخت برای سفارش {order_id}: \n"
                f"کاربر: {user_id}\n"
                f"پلن: {plan['name']}\n"
                f"مبلغ: {plan['price']} تومان"
            )
            logger.debug(
                f"Caption: {caption}, Length: {len(caption.encode('utf-8'))} bytes"
            )
            receipt_message = await bot.send_photo(
                ADMIN_TELEGRAM_ID,
                photo=message.photo[-1].file_id,
                caption=caption,
                reply_markup=get_receipt_admin_menu(order_id),
            )
            await bot.send_message(
                ADMIN_TELEGRAM_ID,
                f"لینک رسید: {receipt_url}",
            )
            await update_order(
                order_id,
                {
                    "receipt_url": receipt_url,
                    "receipt_message_id": receipt_message.message_id,
                    "status": "pending",
                    "telegram_id": user_id,
                },
            )
            await message.reply(
                "رسید شما برای ادمین ارسال شد! منتظر تأیید باشید.",
                reply_markup=get_main_menu(),
            )
    except Exception as e:
        logger.error(f"Failed to process receipt for order {order_id}: {e}")
        await message.reply(
            f"خطا در ذخیره رسید! لطفاً دوباره تلاش کنید.: {str(e)}",
            reply_markup=get_main_menu(),
        )


@router.callback_query(lambda c: c.data.startswith(("confirm_", "reject_")))
async def process_order_action(callback: CallbackQuery, bot: Bot):
    if not await is_admin(callback.from_user.id):
        await callback.answer(
            "❌ فقط ادمین می‌تونه این عملیات رو انجام بده!", show_alert=True
        )
        return
    if callback.data:
        action, order_id = callback.data.split("_")

        logger.info(f"Processing {action} for order {order_id}")

        try:
            order = await get_order(order_id)
            telegram_id = order.get("telegram_id")
            if not telegram_id or not isinstance(telegram_id, int):
                logger.error(f"Invalid or missing telegram_id for order {order_id}")
                await callback.answer("❌ telegram_id نامعتبر است!", show_alert=True)
                return
            plan_id, is_renewal = order["plan_id"], order.get("is_renewal", False)
            plan = get_plan_by_id(plan_id)
            if not plan:
                logger.error(f"Invalid plan: {plan_id}")
                await callback.answer("❌ پلن نامعتبره!", show_alert=True)
                return
            logger.info(f"Order {order_id} fetched successfully")
        except Exception as e:
            logger.error(f"Failed to fetch order {order_id}: {e}")
            await callback.answer("❌ سفارش یافت نشد!", show_alert=True)
            return

        if action == "confirm":
            try:
                existing_user = await get_user_by_telegram_id(telegram_id)
                if existing_user:
                    username = str(existing_user.get("username"))
                    data_limit = int(plan["data_limit"])
                    expire_days = int(plan["expire_days"])
                    users = plan["users"]
                    user_info = await renew_user(
                        telegram_id,
                        username,
                        data_limit,
                        expire_days,
                        users,
                    )
                else:
                    username = f"user_{uuid.uuid4().hex[:8]}"
                    data_limit = int(plan["data_limit"])
                    expire_days = int(plan["expire_days"])
                    users = plan["users"]
                    user_info = await create_user(
                        telegram_id,
                        username,
                        data_limit,
                        expire_days,
                        users,
                    )

                if user_info and "subscription_url" in user_info:
                    token = user_info["subscription_url"].split("/")[-2]
                    await save_user_token(telegram_id, token, username)
                    await update_order(
                        order_id, {"status": "confirmed", "telegram_id": telegram_id}
                    )
                    message_text = (
                        (
                            f"✅ **تمدید اکانت شما تأیید شد!** 🎉\n"
                            f"👤 **نام کاربری**: {username}\n"
                            f"📈 **حجم**: {data_limit / 1073741824 if data_limit else '♾️ نامحدود'} گیگابایت\n"
                            f"⏳ **مدت**: {expire_days if expire_days else 'لایف‌تایم'} روز\n"
                            f"🔗 **لینک اشتراک**: {user_info['subscription_url']}\n"
                            f"لطفاً این لینک رو ذخیره کن یا از /getlink برای دریافت مجدد استفاده کن."
                        )
                        if existing_user or is_renewal
                        else (
                            f"✅ **سفارش شما تأیید شد!** 🎉\n"
                            f"👤 **نام کاربری**: {username}\n"
                            f"📈 **حجم**: {data_limit / 1073741824 if data_limit else '♾️ نامحدود'} گیگابایت\n"
                            f"⏳ **مدت**: {expire_days if expire_days else 'لایف‌تایم'} روز\n"
                            f"🔗 **لینک اشتراک**: {user_info['subscription_url']}\n"
                            f"لطفاً این لینک رو ذخیره کن یا از /getlink برای دریافت مجدد استفاده کن."
                        )
                    )
                    await bot.send_message(
                        telegram_id,
                        message_text,
                        parse_mode="markdown",
                        reply_markup=get_main_menu(),
                    )
                    if (
                        isinstance(callback.message, Message)
                        and callback.message.caption
                    ):
                        await callback.message.edit_caption(
                            caption=callback.message.caption
                            + "\n\n✅ **وضعیت**: تأیید شده",
                            parse_mode="Markdown",
                        )
                    await callback.answer(
                        "سفارش تأیید شد و اکانت برای کاربر ایجاد/تمدید شد!"
                    )
                else:
                    logger.error(
                        f"Failed to {'renew' if existing_user else 'create'} user for order {order_id}: {user_info}"
                    )
                    await callback.answer(
                        f"خطا در {'تمدید' if existing_user else 'ایجاد'} اکانت: {user_info}",
                        show_alert=True,
                    )
            except Exception as e:
                logger.error(f"Failed to confirm order {order_id}: {e}")
                await callback.answer(
                    f"❌ خطا در تأیید سفارش: {str(e)}", show_alert=True
                )
        else:
            try:
                await update_order(
                    order_id, {"status": "rejected", "telegram_id": telegram_id}
                )
                await bot.send_message(
                    telegram_id,
                    f"{'تمدید' if is_renewal else 'سفارش'} *{order_id}* توسط ادمین رد شد. 😔",
                    parse_mode="markdown",
                )
                if isinstance(callback.message, Message) and callback.message.caption:
                    await callback.message.edit_caption(
                        caption=callback.message.caption + "\n\n❌ **وضعیت**: رد شده",
                        parse_mode="Markdown",
                    )
                await callback.answer("سفارش رد شد!")
            except Exception as e:
                logger.error(f"Failed to reject order {order_id}: {e}")
                await callback.answer(f"❌ خطا در رد سفارش: {str(e)}", show_alert=True)
