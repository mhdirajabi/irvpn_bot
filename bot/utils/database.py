import asyncpg
from config import DB_DSN
from datetime import datetime, timedelta


async def get_db_connection():
    return await asyncpg.connect(dsn=DB_DSN)


async def create_user(telegram_id, username):
    conn = await get_db_connection()
    try:
        await conn.execute(
            "INSERT INTO core_botuser (telegram_id, username, joined_date) VALUES ($1, $2, $3) ON CONFLICT (telegram_id) DO NOTHING",
            telegram_id,
            username,
            datetime.now(),
        )
    finally:
        await conn.close()


async def create_order(user_id, plan_id):
    conn = await get_db_connection()
    try:
        order_id = await conn.fetchval(
            "INSERT INTO core_order (user_id, plan_id, payment_status, created_at) VALUES ($1, $2, $3, $4) RETURNING id",
            user_id,
            plan_id,
            "pending",
            datetime.now(),
        )
        return order_id
    finally:
        await conn.close()


async def update_order_receipt(order_id, file_path):
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE core_order SET receipt_file = $1 WHERE id = $2", file_path, order_id
        )
    finally:
        await conn.close()


async def get_latest_pending_order(user_id):
    conn = await get_db_connection()
    try:
        order = await conn.fetchrow(
            "SELECT id, plan_id FROM core_order WHERE user_id = $1 AND payment_status = 'pending' ORDER BY created_at DESC LIMIT 1",
            user_id,
        )
        return order
    finally:
        await conn.close()


async def get_verified_orders_without_config():
    conn = await get_db_connection()
    try:
        orders = await conn.fetch(
            "SELECT o.id, o.user_id, o.plan_id, bu.telegram_id FROM core_order o JOIN core_botuser bu ON o.user_id = bu.id WHERE o.payment_status = 'verified' AND o.marzban_config_id = ''"
        )
        return orders
    finally:
        await conn.close()


async def update_order_config(order_id, config_id):
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE core_order SET marzban_config_id = $1 WHERE id = $2",
            config_id,
            order_id,
        )
    finally:
        await conn.close()


async def get_expired_pending_orders():
    conn = await get_db_connection()
    try:
        orders = await conn.fetch(
            "SELECT o.id, bu.telegram_id FROM core_order o JOIN core_botuser bu ON o.user_id = bu.id WHERE o.payment_status = 'pending' AND o.created_at < $1",
            datetime.now() - timedelta(minutes=30),
        )
        return orders
    finally:
        await conn.close()


async def cancel_order(order_id):
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE core_order SET payment_status = 'canceled' WHERE id = $1", order_id
        )
    finally:
        await conn.close()


async def get_plans():
    conn = await get_db_connection()
    try:
        plans = await conn.fetch("SELECT id, name, price, duration_days FROM core_plan")
        return plans
    finally:
        await conn.close()
