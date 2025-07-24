from django.db import models


class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    subscription_token = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.telegram_id})"


class Order(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("rejected", "Rejected"),
    )
    telegram_id = models.BigIntegerField()
    order_id = models.CharField(max_length=36, unique=True)
    plan_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    receipt_url = models.URLField(blank=True, null=True)
    receipt_message_id = models.BigIntegerField(blank=True, null=True)
    is_renewal = models.BooleanField(default=False)
    price = models.IntegerField(default=0)

    def __str__(self):
        return f"Order {self.order_id} ({self.status})"
