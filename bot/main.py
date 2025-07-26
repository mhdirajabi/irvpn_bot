import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.admin import router as admin_router
from handlers.buy import router as buy_router
from handlers.getlink import router as getlink_router
from handlers.receipt import router as receipt_router
from handlers.renew import router as renew_router
from handlers.start import router as start_router
from handlers.status import router as status_router
from middlewares.log_all_callbacks import log_all_callbacks
from services.background_tasks import check_expiring_users, check_pending_orders
from utils.logger import logger


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.outer_middleware()(log_all_callbacks)

    # ثبت routerها
    dp.include_router(start_router)
    dp.include_router(buy_router)
    dp.include_router(renew_router)
    dp.include_router(status_router)
    dp.include_router(getlink_router)
    dp.include_router(admin_router)
    dp.include_router(receipt_router)

    # شروع تسک‌های پس‌زمینه
    asyncio.create_task(check_pending_orders(bot))
    asyncio.create_task(check_expiring_users(bot))

    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Bot failed: {str(e)}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
