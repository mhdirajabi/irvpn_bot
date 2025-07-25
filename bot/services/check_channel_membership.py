from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from config import CHANNEL_ID
from utils.logger import logger


async def check_channel_membership(bot: Bot, user_id: int) -> bool:
    try:
        if CHANNEL_ID is not None:
            member = await bot.get_chat_member(CHANNEL_ID, user_id)
            return member.status in ["member", "administrator", "creator"]
        else:
            return False
    except TelegramBadRequest as e:
        logger.error(f"Error checking channel membership for user {user_id}: {str(e)}")
        return False
