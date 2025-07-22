import requests
from config import ADMIN_PASSWORD, ADMIN_USERNAME, API_BASE_URL


def get_jwt_token():
    url = f"{API_BASE_URL}/admin/token"
    data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
        "grant_type": "password",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=data, headers=headers, timeout=2000)
    if response.status_code == 200:
        return response.json()["access_token"]
    raise Exception(f"Failed to get JWT token: {response.text}")


API_TOKEN = get_jwt_token()
