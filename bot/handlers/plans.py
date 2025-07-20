from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.database import get_plans, create_order

router = Router()


class BotStates(StatesGroup):
    WAITING_FOR_RECEIPT = State()


@router.message(Command("plans"))
async def plans_handler(message: types.Message):
    plans = await get_plans()
    keyboard = types.InlineKeyboardMarkup()
    for plan in plans:
        keyboard.add(
            types.InlineKeyboardButton(
                f"{plan['name']} - {plan['price']} تومان",
                callback_data=f"plan_{plan['id']}",
            )
        )
    await message.reply("پلن مورد نظرتون رو انتخاب کنید:", reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith("plan_"))
async def select_plan_handler(callback_query: types.CallbackQuery, state: FSMContext):
    plan_id = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id
    order_id = await create_order(user_id, plan_id)
    await state.update_data(order_id=order_id)
    await callback_query.message.reply(
        "لطفاً مبلغ رو به شماره کارت زیر واریز کنید و عکس رسید رو در ۳۰ دقیقه بفرستید:\n`1234-5678-9012-3456`",
        parse_mode="Markdown",
    )
    await state.set_state(BotStates.WAITING_FOR_RECEIPT)
