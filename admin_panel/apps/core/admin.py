from django.contrib import admin

from .models import Order, User


class OrderAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "order_id", "plan_id", "status", "created_at")
    list_filter = ("status",)
    actions = ["verify_payment", "reject_payment"]

    @admin.action(description="تأیید پرداخت")
    def verify_payment(self, request, queryset):
        queryset.update(status="verified")

    @admin.action(description="رد پرداخت")
    def reject_payment(self, request, queryset):
        queryset.update(status="rejected")


admin.site.register(User)
admin.site.register(Order, OrderAdmin)
