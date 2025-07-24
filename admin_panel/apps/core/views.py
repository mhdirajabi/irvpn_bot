import logging
from datetime import datetime, timedelta

from django.db.models import Sum
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, User
from .serializers import OrderSerializer, UserSerializer

logger = logging.getLogger("core")

logger.setLevel(logging.DEBUG)

log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)


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
                telegram_id = int(telegram_id)
                queryset = queryset.filter(telegram_id=telegram_id)
            except ValueError:
                logger.error(f"Invalid telegram_id: {telegram_id}")
                return Response(
                    {"error": "Invalid telegram_id"}, status=status.HTTP_400_BAD_REQUEST
                )
        if status_param:
            status_param = status_param.strip()
            queryset = queryset.filter(status=status_param)

        logger.info(f"Queryset after filtering: {list(queryset.values())}")
        serializer = OrderSerializer(queryset, many=True)
        logger.info(f"Returning {queryset.count()} orders: {serializer.data}")
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
    def get(self, request, order_id):
        logger.debug(f"Fetching order {order_id}")
        try:
            order = Order.objects.get(order_id=order_id)
            serializer = OrderSerializer(order)
            logger.info(f"Order {order_id} fetched: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            logger.error(f"Order not found: {order_id}")
            return Response(
                {"error": f"Order with order_id {order_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, order_id):
        logger.debug(f"Updating order {order_id} with data: {request.data}")
        try:
            order = Order.objects.get(order_id=order_id)
            serializer = OrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Order {order_id} updated: {serializer.data}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            logger.error(f"Invalid data for order {order_id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            logger.error(f"Order not found: {order_id}")
            return Response(
                {"error": f"Order with order_id {order_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptUploadView(APIView):
    def post(self, request):
        logger.debug(f"Uploading receipt with data: {request.data}")
        serializer = OrderSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            logger.error(f"Invalid receipt data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = request.data.get("order_id")
        try:
            order = Order.objects.get(order_id=order_id)
            serializer = OrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Receipt updated for order {order_id}: {serializer.data}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            logger.error(f"Invalid data for order {order_id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            logger.error(f"Order not found: {order_id}")
            return Response(
                {"error": f"Order with order_id {order_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error updating receipt for order {order_id}: {str(e)}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
