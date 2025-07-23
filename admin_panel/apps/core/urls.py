from django.urls import path

from .views import (
    OrderListCreateView,
    OrderUpdateView,
    ReceiptUploadView,
    ReportView,
    UserListCreateView,
)

urlpatterns = [
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
    path("users/<int:telegram_id>/", UserListCreateView.as_view(), name="user-update"),
    path("orders/", OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<str:order_id>/", OrderUpdateView.as_view(), name="order-update"),
    path("receipts/", ReceiptUploadView.as_view(), name="receipt-upload"),
    path("reports/", ReportView.as_view(), name="reports"),
]
