from typing import Any, Awaitable, Callable, Dict

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject, Update
from utils.logger import logger


class LogAllCallbackMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Update) and event.callback_query:
            logger.info(
                f"Received callback query: {event.callback_query.data} from user {event.callback_query.from_user.id}"
            )
        return await handler(event, data)
