from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from config import CHANNEL_ID


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📊 وضعیت اکانت"),
                KeyboardButton(text="🛒 خرید اکانت"),
            ],
            [
                KeyboardButton(text="🔄 تمدید اکانت"),
                KeyboardButton(text="🔗 دریافت لینک"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_main_menu_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 وضعیت اکانت", callback_data="main_status"
                ),
                InlineKeyboardButton(text="🛒 خرید اکانت", callback_data="main_buy"),
            ],
            [
                InlineKeyboardButton(text="🔄 تمدید اکانت", callback_data="main_renew"),
                InlineKeyboardButton(
                    text="🔗 دریافت لینک", callback_data="main_getlink"
                ),
            ],
        ]
    )


def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 ایجاد کاربر جدید"),
                KeyboardButton(text="🛜 مدیریت سرورها"),
            ],
            [
                KeyboardButton(text="📊 وضعیت اکانت"),
                KeyboardButton(text="🛒 خرید اکانت"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_admin_menu_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 ایجاد کاربر جدید", callback_data="main_adduser"
                ),
                InlineKeyboardButton(
                    text="🛜 مدیریت سرورها", callback_data="main_servers"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📊 وضعیت اکانت", callback_data="main_status"
                ),
                InlineKeyboardButton(text="🛒 خرید اکانت", callback_data="main_buy"),
            ],
        ]
    )


def get_channel_join_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 عضو شدن در کانال",
                    url=f"https://t.me/{CHANNEL_ID.lstrip('@')}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ چک کردن عضویت", callback_data="check_membership"
                )
            ],
        ]
    )
