from rest_framework import serializers
from .models import User, Order


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["telegram_id", "subscription_token", "username", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "telegram_id",
            "order_id",
            "plan_id",
            "status",
            "created_at",
            "receipt_url",
            "receipt_message_id",
            "is_renewal",
            "price",
        ]
