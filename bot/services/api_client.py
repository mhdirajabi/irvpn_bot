from typing import Optional

import requests
from config import DJANGO_API_URL
from utils.logger import logger


class APIClient:
    @staticmethod
    async def get(
        url: str,
        params: dict = None,
        headers: dict = None,
        base_url: Optional[str] = DJANGO_API_URL,
    ):
        try:
            response = requests.get(
                f"{base_url}{url}",
                params=params,
                headers=headers,
                timeout=5,
                verify=True,
            )
            response.raise_for_status()
            logger.debug(f"GET request successful: {url}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API GET request failed: {url}, error: {e}")
            raise

    @staticmethod
    async def post(
        url: str,
        data: dict,
        headers: dict = None,
        base_url: Optional[str] = DJANGO_API_URL,
    ):
        try:
            response = requests.post(
                f"{base_url}{url}", json=data, headers=headers, timeout=5, verify=True
            )
            response.raise_for_status()
            logger.debug(f"POST request successful: {url}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API POST request failed: {url}, error: {e}")
            raise

    @staticmethod
    async def put(
        url: str,
        data: dict,
        headers: dict = None,
        base_url: Optional[str] = DJANGO_API_URL,
    ):
        try:
            response = requests.put(
                f"{base_url}{url}", json=data, headers=headers, timeout=5, verify=True
            )
            response.raise_for_status()
            logger.debug(f"PUT request successful: {url}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API PUT request failed: {url}, error: {e}")
            raise
