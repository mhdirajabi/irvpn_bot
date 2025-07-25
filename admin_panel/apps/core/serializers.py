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
        fields = [
            "telegram_id",
            "username",
            "data_limit",
            "expire",
            "status",
            "data_limit_reset_strategy",
            "subscription_url",
        ]


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

    def validate(self, attrs):
        logger.debug(f"Validating order data: {attrs}")
        if not isinstance(attrs.get("telegram_id"), int):
            logger.error(f"Invalid telegram_id type: {type(attrs.get('telegram_id'))}")
            raise serializers.ValidationError("telegram_id must be an integer")
        if "status" in attrs and attrs["status"] not in [
            "pending",
            "confirmed",
            "rejected",
        ]:
            logger.error(f"Invalid status: {attrs['status']}")
            raise serializers.ValidationError(
                "Status must be 'pending', 'confirmed', or 'rejected'"
            )
        return attrs
