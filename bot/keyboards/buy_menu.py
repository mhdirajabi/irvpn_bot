from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.formatters import format_data_limit, format_expire_date
from utils.plans import PLANS


def get_buy_menu():
    categories = sorted(set(plan["category"] for plan in PLANS if plan["is_active"]))
    keyboard = []
    # ساخت دکمه‌ها به صورت دوتایی
    for i in range(0, len(categories), 2):
        row = []
        for category in categories[i : i + 2]:
            text = (
                "📈 اکانت حجمی"
                if category == "volume"
                else "♾️ اکانت نامحدود" if category == "unlimited" else "🧪 اکانت تست"
            )
            row.append(InlineKeyboardButton(text=text, callback_data=f"buy_{category}"))
        keyboard.append(row)
    # اضافه کردن دکمه بازگشت
    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅️ بازگشت به منوی اصلی", callback_data="back_to_main"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_plan_menu(category: str):
    # مرتب‌سازی پلن‌ها بر اساس قیمت
    plans = sorted(
        [plan for plan in PLANS if plan["category"] == category and plan["is_active"]],
        key=lambda x: x["price"],
    )
    keyboard = []
    # ساخت دکمه‌ها به صورت دوتایی
    for i in range(0, len(plans), 2):
        row = []
        for plan in plans[i : i + 2]:
            text = (
                f"📦 {plan['name']} ({format_data_limit(plan['data_limit'])}, "
                f"{format_expire_date(plan['expire_days'])})"
            )
            row.append(
                InlineKeyboardButton(text=text, callback_data=f"select_{plan['id']}")
            )
        keyboard.append(row)
    # اضافه کردن دکمه‌های بازگشت
    keyboard.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="buy_back")])
    keyboard.append(
        [InlineKeyboardButton(text="⬅️ منوی اصلی", callback_data="back_to_main")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
