from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.plans import PLANS


def get_renew_menu():
    keyboard = [
        [
            InlineKeyboardButton(text="🛒 اکانت حجمی", callback_data="renew_volume"),
        ],
        [
            InlineKeyboardButton(
                text="♾️ اکانت نامحدود", callback_data="renew_unlimited"
            ),
        ],
        [
            InlineKeyboardButton(text="↩️ بازگشت", callback_data="renew_back"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_renew_plan_menu(category: str):
    plans = [p for p in PLANS if p["category"] == category and p["is_active"]]
    plans.sort(key=lambda x: x["price"])
    keyboard = []
    for i, plan in enumerate(plans):
        text = (
            f"{plan['data_limit'] // 1073741824}G {plan['expire_days']}D - {plan['price'] // 1000}K"
            if plan["data_limit"]
            else f"∞ {plan['users']}U {plan['expire_days']}D"
        )
        callback_data = f"renewselect_{plan['id']}"
        row = [InlineKeyboardButton(text=text, callback_data=callback_data)]
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="↩️ بازگشت", callback_data="renew_back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
