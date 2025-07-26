from datetime import datetime, timedelta
from typing import Optional

from config import API_BASE_URL, DJANGO_API_URL
from services.api_client import APIClient
from utils.logger import logger
from utils.marzban import get_jwt_token


async def get_subscription_info(token: str):
    try:
        response = await APIClient.get(f"/sub/{token}/info", base_url=API_BASE_URL)
        return response
    except Exception as e:
        logger.error(f"Failed to fetch subscription info for token={token}: {e}")
        return None


async def get_user_by_telegram_id(telegram_id: Optional[int]) -> Optional[dict]:
    try:
        users = await APIClient.get(
            "/users/",
            params={"telegram_id": telegram_id},
            base_url=DJANGO_API_URL,
        )
        return users[0] if users else None
    except Exception as e:
        logger.error(f"Failed to fetch user by telegram_id={telegram_id}: {e}")
        raise


async def get_user_data(telegram_id: int) -> tuple:
    try:
        users = await APIClient.get(
            "/users/",
            params={"telegram_id": telegram_id},
            base_url=DJANGO_API_URL,
        )
        if users:
            return (users[0]["subscription_token"], users[0]["username"])
        return (None, None)
    except Exception as e:
        logger.error(f"Failed to fetch user data for telegram_id={telegram_id}: {e}")
        return (None, None)


async def save_user_token(telegram_id: int, token: str, username: str):
    try:
        # چک کردن وجود کاربر
        user = await get_user_by_telegram_id(telegram_id)
        if user:
            await APIClient.put(
                f"/users/{username}/",
                {
                    "telegram_id": telegram_id,
                    "subscription_token": token,
                    "username": username,
                },
                base_url=DJANGO_API_URL,
            )
            logger.info(
                f"User token updated for telegram_id={telegram_id}, username={username}"
            )
        else:
            await APIClient.post(
                "/users/",
                {
                    "telegram_id": telegram_id,
                    "subscription_token": token,
                    "username": username,
                },
                base_url=DJANGO_API_URL,
            )
            logger.info(
                f"User token saved for telegram_id={telegram_id}, username={username}"
            )
    except Exception as e:
        logger.error(f"Failed to save user token for telegram_id={telegram_id}: {e}")
        raise


async def create_user(
    username: str,
    data_limit: int,
    expire_days: int,
    users: str,
    telegram_id: int = None,
):
    logger.debug(
        f"Creating user {username} with data_limit={data_limit}, expire_days={expire_days}, users={users}"
    )
    headers = {
        "Authorization": f"Bearer {get_jwt_token()}",
        "Content-Type": "application/json",
    }
    expire_timestamp = (
        0
        if expire_days == 0
        else int((datetime.now() + timedelta(days=expire_days)).timestamp())
    )
    inbounds = {"vless": ["IR_SV"]}
    if users == "double":
        inbounds = {"vless": ["IR_SV", "SERVER-KHAREJ"]}
    payload = {
        "username": username,
        "proxies": {"vless": {}},
        "inbounds": inbounds,
        "data_limit": data_limit if data_limit else None,
        "expire": expire_timestamp,
        "status": "active",
        "data_limit_reset_strategy": "no_reset",
    }
    try:
        user_info = await APIClient.post(
            "/api/user", payload, headers=headers, base_url=API_BASE_URL
        )
        logger.info(f"User {username} created successfully: {user_info}")
        try:
            existing_user = await get_user_by_telegram_id(telegram_id)
            django_payload = {
                "telegram_id": telegram_id,
                "username": username,
                "data_limit": data_limit,
                "expire": expire_timestamp,
                "status": "active",
                "data_limit_reset_strategy": "no_reset",
                "subscription_url": user_info.get("subscription_url", ""),
            }
            if existing_user:
                await APIClient.put(
                    f"/users/{username}/",
                    django_payload,
                    base_url=DJANGO_API_URL,
                )
                logger.info(f"User {username} updated in Django")
            else:
                await APIClient.post("/users/", django_payload, base_url=DJANGO_API_URL)
                logger.info(f"User {username} saved in Django")
        except Exception as e:
            logger.error(f"Failed to save user {username} in Django: {e}")
        return user_info
    except Exception as e:
        logger.error(f"Failed to create user {username}: {e}")
        return None


async def renew_user(
    username: str,
    data_limit: int,
    expire_days: int,
    users: str,
    telegram_id: int = None,
):
    logger.debug(
        f"Renewing user {username} with data_limit={data_limit}, expire_days={expire_days}, users={users}"
    )
    headers = {
        "Authorization": f"Bearer {get_jwt_token()}",
        "Content-Type": "application/json",
    }
    expire_timestamp = (
        0
        if expire_days == 0
        else int((datetime.now() + timedelta(days=expire_days)).timestamp())
    )
    inbounds = {"vless": ["IR_SV"]}
    if users == "double":
        inbounds = {"vless": ["IR_SV", "SERVER-KHAREJ"]}
    payload = {
        "data_limit": data_limit if data_limit else None,
        "expire": expire_timestamp,
        "inbounds": inbounds,
        "status": "active",
        "data_limit_reset_strategy": "no_reset",
    }
    try:
        user_info = await APIClient.put(
            f"/api/user/{username}", payload, headers=headers, base_url=API_BASE_URL
        )
        logger.info(f"User {username} renewed successfully: {user_info}")
        try:
            django_payload = {
                "telegram_id": telegram_id,
                "username": username,
                "data_limit": data_limit,
                "expire": expire_timestamp,
                "status": "active",
                "data_limit_reset_strategy": "no_reset",
                "subscription_url": user_info.get("subscription_url", ""),
            }
            await APIClient.put(
                f"/users/{username}",
                django_payload,
                base_url=DJANGO_API_URL,
            )
            logger.info(f"User {username} updated in Django")
        except Exception as e:
            logger.error(f"Failed to update user {username} in Django: {e}")
        return user_info
    except Exception as e:
        logger.error(f"Failed to renew user {username}: {e}")
        return None
