import aiohttp
from config import MARZBAN_API_URL  # MARZBAN_API_TOKEN
from datetime import datetime, timedelta


async def get_admin_token(admin_username, admin_password):
    async with aiohttp.ClientSession() as session:
        url = f"{MARZBAN_API_URL}/api/admin/token"
        username = admin_username
        password = admin_password
        data = {"username": username, "password": password}
        async with session.post(url, json=data) as response:
            if response.status == 200:
                print(type(response))
            return None


# async def create_marzban_config(order_id, duration_days):
#     async with aiohttp.ClientSession() as session:
#         url = f"{MARZBAN_API_URL}/api/users"
#         headers = {"Authorization": f"Bearer {MARZBAN_API_TOKEN}"}
#         username = f"user_{order_id}"
#         data = {
#             "username": username,
#             "expire": int((datetime.now() + timedelta(days=duration_days)).timestamp()),
#             # فرض بر اینه که API مرزبان این فرمت رو قبول می‌کنه
#         }
#         async with session.post(url, json=data, headers=headers) as response:
#             if response.status == 201:
#                 return username
#             return None


# async def get_marzban_config(username):
#     async with aiohttp.ClientSession() as session:
#         url = f"{MARZBAN_API_URL}/api/users/{username}/config"
#         headers = {"Authorization": f"Bearer {MARZBAN_API_TOKEN}"}
#         async with session.get(url, headers=headers) as response:
#             if response.status == 200:
#                 return await response.text()
#             return "خطا در دریافت کانفیگ"
