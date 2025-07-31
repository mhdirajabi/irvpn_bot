from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.plans import PLANS


def get_buy_menu():
    keyboard = [
        [
            InlineKeyboardButton(text="🛒 اکانت حجمی", callback_data="buy_volume"),
        ],
        [
            InlineKeyboardButton(text="♾️ اکانت نامحدود", callback_data="buy_unlimited"),
        ],
        [
            InlineKeyboardButton(text="🎯 اکانت تست", callback_data="buy_test"),
        ],
        [
            InlineKeyboardButton(
                text="↩️ بازگشت به منوی اصلی", callback_data="buy_back"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_plan_menu(category: str):
    plans = [p for p in PLANS if p["category"] == category and p["is_active"]]
    plans.sort(key=lambda x: x["price"])
    keyboard = []
    for i, plan in enumerate(plans):
        if plan["expire_days"] != 0:
            text = (
                f"📊 حجم {plan['data_limit'] // 1073741824} گیگ - {plan['expire_days']} روزه - {plan['price']} تومان"
                if plan["data_limit"]
                else f"♾️ نامحدود {plan['users']} کاربره - {plan['expire_days']} روزه"
            )
        else:
            # For lifetime plans, we can use a different text format
            text = (
                f"📊 حجم {plan['data_limit'] // 1073741824} گیگ - لایف‌تایم - {plan['price']} تومان"
                if plan["data_limit"]
                else f"♾️ نامحدود {plan['users']} کاربره - {plan['expire_days']} روزه"
            )

        callback_data = f"select_{plan['id']}"
        row = [InlineKeyboardButton(text=text, callback_data=callback_data)]
        keyboard.append(row)
    keyboard.append(
        [
            InlineKeyboardButton(
                text="↩️ بازگشت به منوی قبلی", callback_data="select_back"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
