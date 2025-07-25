from config import DJANGO_API_URL
from services.api_client import APIClient
from utils.logger import logger


async def save_order(
    telegram_id: int,
    order_id: str,
    plan_id: str,
    plan_type: str,
    price: int,
    is_renewal: bool = False,
):
    data = {
        "telegram_id": telegram_id,
        "order_id": order_id,
        "plan_id": f"{plan_type}:{plan_id}",
        "status": "pending",
        "price": price,
        "is_renewal": is_renewal,
    }
    logger.debug(f"Sending order to Django: {data}")
    try:
        response = await APIClient.post("/orders/", data, base_url=DJANGO_API_URL)
        logger.info(f"Order saved successfully: {order_id}, response: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to save order: {e}")
        raise


async def update_order(order_id: str, data: dict):
    try:
        response = await APIClient.put(
            f"/orders/{order_id}/", data, base_url=DJANGO_API_URL
        )
        logger.info(f"Order {order_id} updated: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to update order {order_id}: {e}")
        raise


async def get_order(order_id: str):
    try:
        response = await APIClient.get(f"/orders/{order_id}/", base_url=DJANGO_API_URL)
        logger.info(f"Order {order_id} fetched: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to fetch order {order_id}: {e}")
        raise


async def get_pending_orders(telegram_id: str):
    try:
        orders = await APIClient.get(
            "/orders/",
            params={"telegram_id": telegram_id, "status": "pending"},
            base_url=DJANGO_API_URL,
        )
        logger.info(f"Pending orders fetched for telegram_id={telegram_id}: {orders}")
        return orders
    except Exception as e:
        logger.error(
            f"Failed to fetch pending orders for telegram_id={telegram_id}: {e}"
        )
        return []


async def get_orders(telegram_id: str):
    try:
        orders = await APIClient.get(
            "/orders/", params={"telegram_id": telegram_id}, base_url=DJANGO_API_URL
        )
        logger.info(f"Orders fetched for telegram_id={telegram_id}: {orders}")
        return orders
    except Exception as e:
        logger.error(f"Failed to fetch orders for telegram_id={telegram_id}: {e}")
        return []
