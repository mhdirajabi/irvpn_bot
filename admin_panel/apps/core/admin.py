from django.contrib import admin
from .models import Plan, BotUser, Order


class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "plan", "payment_status", "created_at")
    list_filter = ("payment_status",)
    actions = ["verify_payment", "reject_payment"]

    def verify_payment(self, request, queryset):
        queryset.update(payment_status="verified")

    verify_payment.short_description = "تأیید پرداخت"

    def reject_payment(self, request, queryset):
        queryset.update(payment_status="rejected")

    reject_payment.short_description = "رد پرداخت"


admin.site.register(Plan)
admin.site.register(BotUser)
admin.site.register(Order, OrderAdmin)
