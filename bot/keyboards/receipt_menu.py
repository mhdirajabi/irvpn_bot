from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_receipt_admin_menu(
    order_id: str,
    tg_username: Optional[str] = None,
    tg_userfn_clean: Optional[str] = None,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ تأیید",
                    callback_data=f"confirm_{order_id}/{tg_username or ''}/{tg_userfn_clean or ''}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ رد",
                    callback_data=f"reject/{order_id}/{tg_username or ''}/{tg_userfn_clean or ''}",
                )
            ],
        ]
    )
