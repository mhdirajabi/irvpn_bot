from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_receipt_admin_menu(order_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ تأیید", callback_data=f"confirm_{order_id}"
                )
            ],
            [InlineKeyboardButton(text="❌ رد", callback_data=f"reject_{order_id}")],
        ]
    )
