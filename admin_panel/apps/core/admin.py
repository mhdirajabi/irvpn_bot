from django.contrib import admin

from .models import Order, User


class OrderAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "order_id", "plan_id", "status", "created_at")
    list_filter = ("status",)
    actions = ["verify_payment", "reject_payment"]

    def verify_payment(self, request, queryset):
        queryset.update(status="verified")

    verify_payment.short_description = "تأیید پرداخت"

    def reject_payment(self, request, queryset):
        queryset.update(status="rejected")

    reject_payment.short_description = "رد پرداخت"


admin.site.register(User)
admin.site.register(Order, OrderAdmin)
