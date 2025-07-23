PLANS = {
    "volume": {
        "v1m20gb": {
            "data_limit": 20 * 1073741824,
            "expire_days": 30,
            "price": 130000,
            "users": "unlimited",
        },
        "v1m30gb": {
            "data_limit": 30 * 1073741824,
            "expire_days": 30,
            "price": 180000,
            "users": "unlimited",
        },
        "v1m60gb": {
            "data_limit": 60 * 1073741824,
            "expire_days": 30,
            "price": 310000,
            "users": "unlimited",
        },
        "v3m80gb": {
            "data_limit": 80 * 1073741824,
            "expire_days": 90,
            "price": 380000,
            "users": "unlimited",
        },
        "v3m120gb": {
            "data_limit": 120 * 1073741824,
            "expire_days": 90,
            "price": 480000,
            "users": "unlimited",
        },
        "v3m180gb": {
            "data_limit": 180 * 1073741824,
            "expire_days": 90,
            "price": 560000,
            "users": "unlimited",
        },
        "vlifetime100gb": {
            "data_limit": 100 * 1073741824,
            "expire_days": 0,
            "price": 550000,
            "users": "unlimited",
        },
        "vlifetime200gb": {
            "data_limit": 200 * 1073741824,
            "expire_days": 0,
            "price": 980000,
            "users": "unlimited",
        },
    },
    "unlimited": {
        "u1m1user": {
            "data_limit": 0,
            "expire_days": 30,
            "price": 160000,
            "users": "single",
        },
        "u1m2users": {
            "data_limit": 0,
            "expire_days": 30,
            "price": 199000,
            "users": "double",
        },
        "u3m2users": {
            "data_limit": 0,
            "expire_days": 90,
            "price": 590000,
            "users": "double",
        },
    },
    "test": {
        "test1gb": {
            "data_limit": 1 * 1073741824,
            "expire_days": 1,
            "price": 0,
            "users": "single",
        }
    },
}
