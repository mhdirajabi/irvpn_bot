import asyncio
from aiogram import Bot, Dispatcher
from config import TELEGRAM_TOKEN
from handlers.start import router as start_router
from handlers.plans import router as plans_router
from handlers.payment import router as payment_router
from utils.marzban import create_marzban_config, get_marzban_config
from utils.database import (
    get_verified_orders_without_config,
    update_order_config,
    get_expired_pending_orders,
    cancel_order,
)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()


async def check_verified_orders():
    while True:
        await asyncio.sleep(300)  # هر ۵ دقیقه
        orders = await get_verified_orders_without_config()
        for order in orders:
            config_id = await create_marzban_config(
                order["id"], order["plan_id"]
            )  # فرض بر اینه که plan_id شامل مدت زمانه
            if config_id:
                await update_order_config(order["id"], config_id)
                config_details = await get_marzban_config(config_id)
                await bot.send_message(
                    order["telegram_id"], f"کانفیگ شما:\n{config_details}"
                )


async def check_expired_orders():
    while True:
        await asyncio.sleep(300)  # هر ۵ دقیقه
        orders = await get_expired_pending_orders()
        for order in orders:
            await cancel_order(order["id"])
            await bot.send_message(
                order["telegram_id"], "سفارش شما به دلیل اتمام مهلت لغو شد."
            )


async def on_startup():
    asyncio.create_task(check_verified_orders())
    asyncio.create_task(check_expired_orders())
    print("ربات شروع شد.")


if __name__ == "__main__":
    dp.include_router(start_router)
    dp.include_router(plans_router)
    dp.include_router(payment_router)
    dp.start_polling(bot, on_startup=on_startup)
