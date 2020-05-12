import logging

from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from sm.core.models import Subscription
from sm.new_frontend.authenticate import HasProfile
from sm.new_frontend.subscriptions.serializer import SubscriptionSerializer, UpsertSubscriptionSerializer
from sm.product.google.utility.subscriptions_utility import get_zoho_products_list_from_response

from sm.product.gsc.zoho import update_account
from .serializer_helpers import remove_subscription

logger = logging.getLogger(__name__)


class ListSubscriptionView(ListAPIView):
    permission_classes = (IsAuthenticated, HasProfile)
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        list_type = self.request.GET.get('layout', 'list')
        customer = self.request.user.sm.customer

        if list_type == 'list':
            queryset = Subscription.objects.filter(customer=customer)
        else:
            queryset = Subscription.objects.filter(customer=customer, parent_subscription=None)

        return queryset


class UpsertDetectedSubscriptionView(UpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UpsertSubscriptionSerializer

    def get_object(self):
        return None

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data"), list):
            kwargs["many"] = True

        return super(UpsertDetectedSubscriptionView, self).get_serializer(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        res = super(UpsertDetectedSubscriptionView, self).update(request, *args, **kwargs)

        # SM-248 update zoho account record with subscriptions info
        customer, vendor_products = get_zoho_products_list_from_response(res)
        if customer is not None and res is not None:
            # TODO: only push if there were actual changes ok
            update_account(customer, vendor_products=vendor_products)
            # remove old subscriptions
            remove_subscription(res)
        return Response({"result": "success"}, status=status.HTTP_200_OK)
