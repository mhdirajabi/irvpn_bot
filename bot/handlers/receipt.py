import uuid

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from config import ADMIN_TELEGRAM_ID, BOT_TOKEN, CHANNEL_ID
from keyboards.main_menu import get_channel_keyboard, get_menu
from keyboards.receipt_menu import get_receipt_admin_menu
from services.check_channel_membership import check_channel_membership
from services.order_service import order_service
from services.user_service import (
    create_user,
    get_user_data,
    renew_user,
    save_user_token,
)
from utils.logger import logger
from utils.plans import PLANS

from bot.handlers.admin import is_admin

router = Router()


@router.message(F.photo)
async def handle_receipt(message: Message, bot: Bot):
    user_id = str(message.from_user.id)
    order_logger.info(f"Handling receipt for user: {user_id}")
    if not await check_channel_membership(bot, user_id):
        order_logger.warning(f"User {user_id} not in channel {CHANNEL_ID}")
        await message.reply(
            f"⚠️ *لطفاً ابتدا در کانال ما عضو شوید*: {CHANNEL_ID}",
            parse_mode="Markdown",
            reply_markup=get_channel_keyboard(),
        )
        return

    try:
        orders = await order_service.get_pending_orders(user_id)
        order_logger.info(f"Orders fetched for user {user_id}: {orders}")
        if not orders:
            order_logger.warning(f"No pending orders found for user {user_id}")
            all_orders = await order_service.get_orders(user_id)
            await message.reply(
                f"⚠️ *هیچ سفارش در حال انتظاری برای شما وجود ندارد!* \n"
                f"لطفاً مطمئن شوید که سفارش خود را ثبت کرده‌اید.\n"
                f"وضعیت سفارش‌ها: {all_orders if all_orders else 'هیچ سفارشی یافت نشد'}",
                parse_mode="markdown",
                reply_markup=get_menu(),
            )
            return
        order = sorted(orders, key=lambda x: x["created_at"], reverse=True)[0]
        order_id, plan_id, is_renewal = (
            order["order_id"],
            order["plan_id"],
            order.get("is_renewal", False),
        )
        plan_type, _ = plan_id.split(":") if ":" in plan_id else (plan_id, plan_id)
        order_logger.debug(
            f"Processing order: {order_id}, plan_id: {plan_id}, is_renewal: {is_renewal}"
        )
    except Exception as e:
        order_logger.error(f"Error checking order for user {user_id}: {e}")
        await message.reply(
            f"❌ *خطا در ارتباط با سرور*: {str(e)}", parse_mode="markdown"
        )
        return

    plan = PLANS.get(plan_type, {}).get(plan_id)
    if not plan:
        order_logger.error(f"Invalid plan: {plan_type}:{plan_id}")
        await message.reply("❌ *پلن نامعتبر است!*", parse_mode="Markdown")
        return

    try:
        file = await bot.get_file(message.photo[-1].file_id)
        receipt_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
        receipt_message = await bot.send_photo(
            ADMIN_TELEGRAM_ID,
            photo=message.photo[-1].file_id,
            caption=(
                f"📥 *رسید پرداخت برای {'تمدید' if is_renewal else 'سفارش'} {order_id}:*\n"
                f"👤 *کاربر*: {user_id}\n"
                f"📦 *پلن*: {plan_id} ({plan_type})\n"
                f"📈 *حجم*: {plan['data_limit'] / 1073741824 if plan['data_limit'] else '♾️ نامحدود'} گیگابایت\n"
                f"⏳ *مدت*: {plan['expire_days'] if plan['expire_days'] else 'لایف‌تایم'} روز\n"
                f"💸 *مبلغ*: {plan['price']} تومان\n"
                f"🔗 *لینک رسید*: {receipt_url}"
            ),
            parse_mode="Markdown",
            reply_markup=get_receipt_admin_menu(order_id),
        )
        order_logger.info(
            f"Receipt sent to admin for order {order_id}, message_id: {receipt_message.message_id}"
        )
        await order_service.update_order(
            order_id,
            {
                "receipt_url": receipt_url,
                "receipt_message_id": receipt_message.message_id,
                "status": "pending",
            },
        )
        await message.reply(
            "✅ *رسید شما برای ادمین ارسال شد! منتظر تأیید باشید.*",
            parse_mode="Markdown",
            reply_markup=get_menu(),
        )
    except Exception as e:
        order_logger.error(f"Failed to process receipt for order {order_id}: {e}")
        await message.reply(
            f"❌ *خطا در ذخیره رسید! لطفاً دوباره تلاش کنید.*: {str(e)}",
            parse_mode="Markdown",
            reply_markup=get_menu(),
        )


@router.callback_query(lambda c: c.data.startswith(("confirm_", "reject_")))
async def process_order_action(callback: CallbackQuery, bot: Bot):
    if not await is_admin(callback.from_user.id):
        await callback.answer(
            "❌ فقط ادمین می‌تونه این عملیات رو انجام بده!", show_alert=True
        )
        return

    action, order_id = callback.data.split("_")
    order_logger.info(f"Processing {action} for order {order_id}")

    try:
        order = await order_service.get_order(order_id)
        telegram_id, plan_id, is_renewal = (
            order["telegram_id"],
            order["plan"],
            order.get("is_renewal", False),
        )
        plan_type, _ = plan_id.split(":") if ":" in plan_id else (plan_id, plan_id)
        order_logger.info(f"Order {order_id} fetched successfully")
    except Exception as e:
        order_logger.error(f"Failed to fetch order {order_id}: {e}")
        await callback.answer("❌ سفارش یافت نشد!", show_alert=True)
        return

    plan = PLANS.get(plan_type, {}).get(plan_id)
    if not plan:
        order_logger.error(f"Invalid plan: {plan_type}:{plan_id}")
        await callback.answer("❌ پلن نامعتبره!", show_alert=True)
        return

    if action == "confirm":
        try:
            token, username = await get_user_data(telegram_id)
            if is_renewal and username:
                user_info = await renew_user(
                    username,
                    plan["data_limit"],
                    plan["expire_days"],
                    plan["users"],
                    telegram_id,
                )
                if user_info and "subscription_url" in user_info:
                    await save_user_token(
                        telegram_id,
                        user_info["subscription_url"].split("/")[-2],
                        username,
                    )
                    await order_service.update_order(order_id, {"status": "confirmed"})
                    await bot.send_message(
                        telegram_id,
                        f"""
                        ✅ **تمدید اکانت شما تأیید شد!** 🎉
                        👤 **نام کاربری**: {username}
                        📈 **حجم**: {plan['data_limit'] / 1073741824 if plan['data_limit'] else '♾️ نامحدود'} گیگابایت
                        ⏳ **مدت**: {plan['expire_days'] if 'expire_days' in plan else 'لایف‌تایم'} روز
                        🔗 **لینک اشتراک**: {user_info['subscription_url']}
                        لطفاً این لینک رو ذخیره کن یا از /getlink برای دریافت مجدد استفاده کن.
                        """,
                        parse_mode="markdown",
                        reply_markup=get_menu(),
                    )
                    await callback.message.edit_caption(
                        caption=callback.message.caption
                        + "\n\n✅ **وضعیت**: تأیید شده",
                        parse_mode="Markdown",
                    )
                    await callback.answer("تمدید اکانت تأیید شد!")
                else:
                    order_logger.error(
                        f"Failed to renew user for order {order_id}: {user_info}"
                    )
                    await callback.answer(
                        f"خطا در تمدید اکانت: {user_info.get('error', 'Unknown error')}",
                        show_alert=True,
                    )
            else:
                username = f"user_{uuid.uuid4().hex[:8]}"
                user_info = await create_user(
                    username,
                    plan["data_limit"],
                    plan["expire_days"],
                    plan["users"],
                    telegram_id,
                )
                if user_info and "subscription_url" in user_info:
                    token = user_info["subscription_url"].split("/")[-2]
                    await save_user_token(telegram_id, token, username)
                    await order_service.update_order(order_id, {"status": "confirmed"})
                    await bot.send_message(
                        telegram_id,
                        f"""
                        ✅ **سفارش شما تأیید شد!** 🎉
                        👤 **نام کاربری**: {username}
                        📈 **حجم**: {plan['data_limit'] / 1073741824 if plan['data_limit'] else '♾️ نامحدود'} گیگابایت
                        ⏳ **مدت**: {plan['expire_days'] if 'expire_days' in plan else 'لایف‌تایم'} روز
                        🔗 **لینک اشتراک**: {user_info['subscription_url']}
                        لطفاً این لینک رو ذخیره کن یا از /getlink برای دریافت مجدد استفاده کن.
                        """,
                        parse_mode="markdown",
                        reply_markup=get_menu(),
                    )
                    await callback.message.edit_caption(
                        caption=callback.message.caption
                        + "\n\n✅ **وضعیت**: تأیید شده",
                        parse_mode="Markdown",
                    )
                    await callback.answer("سفارش تأیید شد و اکانت برای کاربر ایجاد شد!")
                else:
                    order_logger.error(
                        f"Failed to create user for order {order_id}: {user_info}"
                    )
                    await callback.answer(
                        f"خطا در ایجاد اکانت: {user_info.get('error', 'Unknown error')}",
                        show_alert=True,
                    )
        except Exception as e:
            order_logger.error(f"Failed to confirm order {order_id}: {e}")
            await callback.answer(f"❌ خطا در تأیید سفارش: {str(e)}", show_alert=True)
    else:  # reject
        try:
            await order_service.update_order(order_id, {"status": "rejected"})
            await bot.send_message(
                telegram_id,
                f"{'تمدید' if is_renewal else 'سفارش'} *{order_id}* توسط ادمین رد شد. 😔",
                parse_mode="markdown",
            )
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\n❌ **وضعیت**: رد شده",
                parse_mode="Markdown",
            )
            await callback.answer("سفارش رد شد!")
        except Exception as e:
            order_logger.error(f"Failed to reject order {order_id}: {e}")
            await callback.answer(f"❌ خطا در رد سفارش: {str(e)}", show_alert=True)
