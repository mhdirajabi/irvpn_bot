from django.db import models


class Plan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()

    def __str__(self):
        return self.name


class BotUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, blank=True)
    joined_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.telegram_id} - {self.username}"


class Order(models.Model):
    user = models.ForeignKey(BotUser, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "در انتظار"),
            ("verified", "تأیید شده"),
            ("rejected", "رد شده"),
            ("canceled", "لغو شده"),
        ],
    )
    receipt_file = models.FileField(upload_to="receipts/", blank=True)
    marzban_config_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Order {self.id} - {self.user}"
