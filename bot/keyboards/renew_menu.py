from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.formatters import format_data_limit, format_expire_date


def get_renew_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📈 اکانت حجمی", callback_data="renew_volume")],
            [
                InlineKeyboardButton(
                    text="♾️ اکانت نامحدود", callback_data="renew_unlimited"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ بازگشت به منوی اصلی", callback_data="back_to_main"
                )
            ],
        ]
    )


def get_renew_plan_menu(account_type: str, plans: dict):
    keyboard = [
        [
            InlineKeyboardButton(
                text=f"📦 پلن {plan_id}: {format_data_limit(plan['data_limit'])}, "
                f"{format_expire_date(plan['expire_days'])}, {plan['price']} تومان",
                callback_data=f"renewselect_{account_type}_{plan_id}",
            )
        ]
        for plan_id, plan in plans.items()
    ]
    keyboard.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="buy_back")])
    keyboard.append(
        [InlineKeyboardButton(text="⬅️ منوی اصلی", callback_data="back_to_main")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
