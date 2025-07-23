from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from .models import User, Order
from .serializers import UserSerializer, OrderSerializer
from django.core.files.storage import FileSystemStorage
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("core")


class UserListCreateView(APIView):
    def get(self, request):
        telegram_id = request.query_params.get("telegram_id")
        if telegram_id:
            users = User.objects.filter(telegram_id=telegram_id)
        else:
            users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, telegram_id):
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderListCreateView(APIView):
    def get(self, request):
        telegram_id = request.query_params.get("telegram_id")
        status_param = request.query_params.get("status")
        logger.debug(
            f"Fetching orders with telegram_id={telegram_id}, status={status_param}"
        )

        queryset = Order.objects.all()
        if telegram_id:
            try:
                queryset = queryset.filter(telegram_id=int(telegram_id))
            except ValueError:
                logger.error(f"Invalid telegram_id: {telegram_id}")
                return Response(
                    {"error": "Invalid telegram_id"}, status=status.HTTP_400_BAD_REQUEST
                )
        if status_param:
            queryset = queryset.filter(status=status_param)

        serializer = OrderSerializer(queryset, many=True)
        logger.info(f"Returning {queryset.count()} orders: {list(queryset.values())}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        logger.debug(f"Creating order with data: {request.data}")
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Order created: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Order creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderUpdateView(APIView):
    def put(self, request, order_id):
        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReceiptUploadView(APIView):
    def post(self, request):
        order_id = request.data.get("order_id")
        file_url = request.data.get("file_url")
        try:
            order = Order.objects.get(order_id=order_id)
            response = requests.get(file_url, timeout=50000)
            if response.status_code == 200:
                fs = FileSystemStorage()
                filename = f"receipts/{order_id}.jpg"
                with open(fs.path(filename), "wb") as f:
                    f.write(response.content)
                receipt_url = fs.url(filename)
                order.receipt_url = receipt_url
                order.save()
                return Response({"receipt_url": receipt_url}, status=status.HTTP_200_OK)
            return Response(
                {"error": "Failed to download file"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )


class ReportView(APIView):
    def get(self, request):
        total_users = User.objects.count()
        total_orders = Order.objects.count()
        confirmed_orders = Order.objects.filter(status="confirmed").count()
        total_revenue = (
            Order.objects.filter(status="confirmed").aggregate(Sum("price"))[
                "price__sum"
            ]
            or 0
        )
        active_users = User.objects.filter(subscription_token__isnull=False).count()
        last_30_days = datetime.now() - timedelta(days=30)
        monthly_revenue = (
            Order.objects.filter(
                status="confirmed", created_at__gte=last_30_days
            ).aggregate(Sum("price"))["price__sum"]
            or 0
        )

        report = {
            "total_users": total_users,
            "total_orders": total_orders,
            "confirmed_orders": confirmed_orders,
            "total_revenue": total_revenue,
            "active_users": active_users,
            "monthly_revenue": monthly_revenue,
        }
        return Response(report)
