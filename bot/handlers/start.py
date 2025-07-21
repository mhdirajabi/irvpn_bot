from aiogram import types, Router
from aiogram.filters import CommandStart
from config import CHANNEL_ID
from main import bot
from utils.database import create_user

router = Router()


async def check_channel_membership(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


@router.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    await create_user(user_id, username)
    if not await check_channel_membership(user_id):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("عضو شدم", callback_data="check_join"))
        await message.reply(
            f"لطفاً اول در کانال {CHANNEL_ID} عضو بشید.", reply_markup=keyboard
        )
    else:
        await message.reply("خوش اومدید! برای خرید پلن، /plans رو بزنید.")


@router.callback_query(lambda c: c.data == "check_join")
async def check_join_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if await check_channel_membership(user_id):
        await callback_query.message.reply(
            "عضویت تأیید شد! برای خرید پلن، /plans رو بزنید."
        )
        await callback_query.message.delete()
    else:
        await callback_query.answer("هنوز عضو نشدید!")
