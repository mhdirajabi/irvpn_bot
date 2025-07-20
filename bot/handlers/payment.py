from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import bot, MEDIA_ROOT
import os
from utils.database import get_latest_pending_order, update_order_receipt

router = Router()


class BotStates(StatesGroup):
    WAITING_FOR_RECEIPT = State()


async def download_receipt(file_id, order_id):
    file = await bot.get_file(file_id)
    file_path = file.file_path
    destination = os.path.join(MEDIA_ROOT, "receipts", f"order_{order_id}.jpg")
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    await bot.download_file(file_path, destination)
    return f"receipts/order_{order_id}.jpg"


@router.message(lambda message: message.photo, state=BotStates.WAITING_FOR_RECEIPT)
async def receipt_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    order = await get_latest_pending_order(user_id)
    if order:
        receipt_file_id = message.photo[-1].file_id
        file_path = await download_receipt(receipt_file_id, order["id"])
        await update_order_receipt(order["id"], file_path)
        await message.reply("رسید دریافت شد. منتظر تأیید ادمین باشید.")
        await state.clear()
    else:
        await message.reply("سفارش فعالی پیدا نشد.")
        await state.clear()
