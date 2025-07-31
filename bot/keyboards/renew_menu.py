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
            InlineKeyboardButton(
                text="↩️ بازگشت به منوی اصلی", callback_data="renew_back"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_renew_plan_menu(category: str):
    plans = [p for p in PLANS if p["category"] == category and p["is_active"]]
    plans.sort(key=lambda x: x["price"])
    keyboard = []
    for i, plan in enumerate(plans):
        if plan["expire_days"] != 0 and plan["price"] != 0:
            if plan["users"] == "single":
                text = (
                    f"📊 حجم {plan['data_limit'] // 1073741824} گیگ - {plan['expire_days']} روزه - {plan['price']} تومان"
                    if plan["data_limit"]
                    else f"♾️ نامحدود تک کاربره - {plan['expire_days']} روزه - {plan['price']} تومان"
                )
            else:
                text = (
                    f"📊 حجم {plan['data_limit'] // 1073741824} گیگ - {plan['expire_days']} روزه - {plan['price']} تومان"
                    if plan["data_limit"]
                    else f"♾️ نامحدود دو کاربره - {plan['expire_days']} روزه - {plan['price']} تومان"
                )
        elif plan["expire_days"] == 0:
            if plan["users"] == "single":
                text = (
                    f"📊 حجم {plan['data_limit'] // 1073741824} گیگ - لایف‌تایم - {plan['price']} تومان"
                    if plan["data_limit"]
                    else f"♾️ نامحدود تک کاربره - {plan['expire_days']} روزه - {plan['price']} تومان"
                )
            else:
                text = (
                    f"📊 حجم {plan['data_limit'] // 1073741824} گیگ - لایف‌تایم - {plan['price']} تومان"
                    if plan["data_limit"]
                    else f"♾️ نامحدود دو کاربره - {plan['expire_days']} روزه - {plan['price']} تومان"
                )
        elif plan["price"] == 0:
            if plan["users"] == "single":
                text = (
                    f"📊 حجم {plan['data_limit'] // 1073741824} گیگ - لایف‌تایم - رایگان"
                    if plan["data_limit"]
                    else f"♾️ نامحدود تک کاربره - {plan['expire_days']} روزه - {plan['price']} تومان"
                )
            else:
                text = (
                    f"📊 حجم {plan['data_limit'] // 1073741824} گیگ - لایف‌تایم - رایگان"
                    if plan["data_limit"]
                    else f"♾️ نامحدود دو کاربره - {plan['expire_days']} روزه - {plan['price']} تومان"
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
