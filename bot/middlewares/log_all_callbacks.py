from aiogram.types import Update
from utils.logger import logger


async def log_all_callbacks(handler, event: Update, data: dict):
    if event.callback_query:
        logger.info(
            f"Received callback query: {event.callback_query.data} from user {event.callback_query.from_user.id}"
        )
    return await handler(event, data)
