from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_cancel_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ لغو", callback_data="cancel")]]
    )
