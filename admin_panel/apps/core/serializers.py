import logging

from rest_framework import serializers

from .models import Order, User

logger = logging.getLogger("core")

logger.setLevel(logging.DEBUG)

log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["telegram_id", "subscription_token", "username", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "telegram_id",
            "order_id",
            "plan_id",
            "status",
            "created_at",
            "price",
            "is_renewal",
            "receipt_url",
            "receipt_message_id",
        ]
        read_only_fields = ["created_at"]

    def validate(self, data):
        logger.debug(f"Validating order data: {data}")
        if not isinstance(data.get("telegram_id"), int):
            logger.error(f"Invalid telegram_id type: {type(data.get('telegram_id'))}")
            raise serializers.ValidationError("telegram_id must be an integer")
        if isinstance(data.get("created_at"), str):
            from datetime import datetime

            try:
                datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except ValueError:
                logger.error(f"Invalid created_at format: {data['created_at']}")
                raise serializers.ValidationError(
                    "Invalid created_at format"
                ) from ValueError
        if "status" in data and data["status"] not in [
            "pending",
            "confirmed",
            "rejected",
        ]:
            logger.error(f"Invalid status: {data['status']}")
            raise serializers.ValidationError(
                "Status must be 'pending', 'confirmed', or 'rejected'"
            )
        return data
