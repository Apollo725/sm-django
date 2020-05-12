
import logging

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sm.core.models import (Catalog, Order, OrderStatus, OrderType, Product,
                            Subscription)
from sm.new_frontend.authenticate import HasProfile
from sm.new_frontend.orders import serializers
from sm.product.google.utility.order_util import (create_order_instance,
                                                  create_order_detail_instance,
                                                  order_detail_update,
                                                  order_update)

logger = logging.getLogger(__name__)


class OrderListView(ListAPIView):
    serializer_class = serializers.OrderListSerializer
    permission_classes = (IsAuthenticated, HasProfile)

    def get_queryset(self):
        return Order.objects \
            .filter(customer=self.request.user.sm.customer) \
            .exclude(status__in=(OrderStatus.CREATED, OrderStatus.DRAFT)) \
            .order_by('-date')


class OrderRetrieveView(RetrieveAPIView):
    serializer_class = serializers.OrderRetrieveSerializer
    permission_classes = (IsAuthenticated, HasProfile)
    lookup_field = 'id'


class OrderDetailView(RetrieveAPIView):
    queryset = Order.objects.prefetch_related('details')
    serializer_class = serializers.OrderDetailsSerializer
    permission_classes = (IsAuthenticated, HasProfile)
    lookup_field = 'id'

    def get_object(self):
        order = super(OrderDetailView, self).get_object()
        if order.status == OrderStatus.DRAFT:
            order_update(order)
        return order


class OrderCreateView(APIView):
    permission_classes = (IsAuthenticated, HasProfile)

    def post(self, request):
        customer = request.user.sm.customer

        details = request.data['details']
        # Get all given products in one request to DB instead of multiple times
        # in loop.
        products = Product.objects.filter(
            id__in=[d['product'] for d in details if d['product']]
        )
        products_mapping = {p.id: p for p in products}
        # Get all given subscriptions in one request to DB instead of multiple
        # times in loop.
        subscriptions = Subscription.objects.filter(
            id__in=[d['subscription'] for d in details if d['subscription']]
        )
        subscriptions_mapping = {s.id: s for s in subscriptions}
        catalog = get_object_or_404(Catalog, id=request.data['catalog'])

        order = create_order_instance(customer)
        order.currency = request.data['currency']
        order.save()
        for detail_data in details:
            product = products_mapping.get(detail_data['product'])
            if product is None and detail_data['product'] is not None:
                raise Http404(
                    'Product with ID "{}" not found.'
                    .format(detail_data['product'])
                )
            subscription = subscriptions_mapping.get(detail_data['subscription'])
            if subscription is None and detail_data['subscription'] is not None:
                raise Http404(
                    'Subscription with ID "{}" not found.'
                    .format(detail_data['subscription'])
                )
            detail = create_order_detail_instance(
                order=order,
                product=product,
                catalog=catalog
            )
            detail.type = OrderType[detail_data['type'].upper()]
            detail.subscription = subscription
            detail.amount = detail_data['amount']
            detail.save()
        order_update(order)
        return Response(
            serializers.OrderDetailsSerializer(
                instance=order,
                many=False
            ).data,
            status=status.HTTP_201_CREATED
        )


class OrderUpdateView(UpdateAPIView):
    permission_classes = (IsAuthenticated, HasProfile)

    def post(self, *args, **kwargs):
        return Response()
