from typing import Dict, Optional

GB_TO_BYTES = 1073741824

PLANS = [
    {
        "id": "volume_20gb_1m",
        "name": "حجم 20 گیگ 1 ماهه",
        "category": "volume",
        "data_limit": 20 * GB_TO_BYTES,
        "expire_days": 30,
        "price": 130000,
        "users": "unlimited",
        "is_active": True,
    },
    {
        "id": "volume_30gb_1m",
        "name": "حجم 30 گیگ 1 ماهه",
        "category": "volume",
        "data_limit": 30 * GB_TO_BYTES,
        "expire_days": 30,
        "price": 180000,
        "users": "unlimited",
        "is_active": True,
    },
    {
        "id": "volume_60gb_1m",
        "name": "حجم 60 گیگ 1 ماهه",
        "category": "volume",
        "data_limit": 60 * GB_TO_BYTES,
        "expire_days": 30,
        "price": 310000,
        "users": "unlimited",
        "is_active": True,
    },
    {
        "id": "volume_80gb_3m",
        "name": "حجم 80 گیگ 3 ماهه",
        "category": "volume",
        "data_limit": 80 * GB_TO_BYTES,
        "expire_days": 90,
        "price": 380000,
        "users": "unlimited",
        "is_active": True,
    },
    {
        "id": "volume_120gb_3m",
        "name": "حجم 120 گیگ 3 ماهه",
        "category": "volume",
        "data_limit": 120 * GB_TO_BYTES,
        "expire_days": 90,
        "price": 480000,
        "users": "unlimited",
        "is_active": True,
    },
    {
        "id": "volume_180gb_3m",
        "name": "حجم 180 گیگ 3 ماهه",
        "category": "volume",
        "data_limit": 180 * GB_TO_BYTES,
        "expire_days": 90,
        "price": 560000,
        "users": "unlimited",
        "is_active": True,
    },
    {
        "id": "volume_100gb_lifetime",
        "name": "حجم 100 گیگ مادام‌العمر",
        "category": "volume",
        "data_limit": 100 * GB_TO_BYTES,
        "expire_days": 0,
        "price": 550000,
        "users": "unlimited",
        "is_active": True,
    },
    {
        "id": "volume_200gb_lifetime",
        "name": "حجم 200 گیگ مادام‌العمر",
        "category": "volume",
        "data_limit": 200 * GB_TO_BYTES,
        "expire_days": 0,
        "price": 980000,
        "users": "unlimited",
        "is_active": True,
    },
    {
        "id": "unlimited_1user_1m",
        "name": "نامحدود 1 کاربره 1 ماهه",
        "category": "unlimited",
        "data_limit": 0,
        "expire_days": 30,
        "price": 160000,
        "users": "single",
        "is_active": True,
    },
    {
        "id": "unlimited_2users_1m",
        "name": "نامحدود 2 کاربره 1 ماهه",
        "category": "unlimited",
        "data_limit": 0,
        "expire_days": 30,
        "price": 199000,
        "users": "double",
        "is_active": True,
    },
    {
        "id": "unlimited_2users_3m",
        "name": "نامحدود 2 کاربره 3 ماهه",
        "category": "unlimited",
        "data_limit": 0,
        "expire_days": 90,
        "price": 590000,
        "users": "double",
        "is_active": True,
    },
    {
        "id": "test_1gb_1d",
        "name": "تست 1 گیگ 1 روزه",
        "category": "test",
        "data_limit": 1 * GB_TO_BYTES,
        "expire_days": 1,
        "price": 0,
        "users": "single",
        "is_active": True,
    },
]


def get_plan_by_id(plan_id: str) -> Optional[Dict[str, str]]:
    """Find a plan by its ID."""
    for plan in PLANS:
        if plan["id"] == plan_id:
            return plan
    return None
