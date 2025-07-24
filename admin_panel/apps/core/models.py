import uuid
from django.db import models


class User(models.Model):
    telegram_id = models.BigIntegerField(null=True, blank=True)
    username = models.CharField(max_length=100, unique=True)
    data_limit = models.BigIntegerField(null=True, blank=True)
    expire = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default="active")
    data_limit_reset_strategy = models.CharField(max_length=50, default="no_reset")
    subscription_url = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_user"

    def __str__(self):
        return f"{self.username} ({self.telegram_id})"


class Order(models.Model):
    telegram_id = models.BigIntegerField()
    order_id = models.UUIDField(default=uuid.uuid4, unique=True)
    plan_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    receipt_url = models.URLField(null=True, blank=True)
    receipt_message_id = models.IntegerField(null=True, blank=True)
    is_renewal = models.BooleanField(default=False)
    price = models.IntegerField()

    class Meta:
        db_table = "core_order"

    def __str__(self):
        return f"Order {self.order_id} ({self.status})"
