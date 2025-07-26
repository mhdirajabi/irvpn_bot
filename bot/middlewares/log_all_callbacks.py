from aiogram.types import Update
from utils.logger import logger


async def log_all_callbacks(update: Update, handler, **kwargs):
    if update.callback_query:
        logger.info(
            f"Received callback query: {update.callback_query.data} from user {update.callback_query.from_user.id}"
        )
    return await handler(update, **kwargs)
