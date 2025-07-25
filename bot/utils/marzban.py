from datetime import datetime, timedelta

import requests
from config import ADMIN_PASSWORD, ADMIN_USERNAME, API_BASE_URL
from utils.logger import logger

_jwt_token = None
_token_expiry = None


def get_jwt_token():
    global _jwt_token, _token_expiry
    if _jwt_token and _token_expiry and datetime.now() < _token_expiry:
        return _jwt_token

    url = f"{API_BASE_URL}/api/admin/token"
    data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
        "grant_type": "password",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(url, data=data, headers=headers, timeout=5)
        response.raise_for_status()
        token_data = response.json()
        _jwt_token = token_data["access_token"]
        # فرض می‌کنیم توکن 1 ساعت اعتبار داره
        _token_expiry = datetime.now() + timedelta(hours=1)
        logger.info("JWT token retrieved successfully")
        return _jwt_token
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get JWT token: {str(e)}")
        raise Exception(f"Failed to get JWT token: {str(e)}") from e
