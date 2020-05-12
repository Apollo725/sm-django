from __future__ import absolute_import

import braintree
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, mixins
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK

from sm.api import serializers, filters, utils
from sm.core import models, promotion, user_token
from sm.core.paypal import billing_plan
from sm.product.gsc.api.apiview.users import get_user_domain
from sm.product.gsc.zoho import create_tmp_lead, convert_lead


logger = logging.getLogger(__name__)


class TokenView(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = [IsAdminUser]
    serializer_class = serializers.UserTokenSerializer
    factory = user_token.user_token_factory

    def get_object(self):
        email = self.kwargs['email']
        customer = self.kwargs.get('customer')
        if customer is None:
            customer_record = models.Customer.objects.filter(name=get_user_domain(email)).order_by("-id").first()
            if customer_record is None:
                raise Http404
            customer = customer_record.name
        logger.info("email: %s, customer: %s", email, customer)

        try:
            models.User.objects.get(email=email, customer__name=customer)
            return user_token.user_token_factory.create(email=email, customer=customer)
        except ObjectDoesNotExist:
            raise Http404


class BraintreeTokenView(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        params = dict()
        customer_id = billing_plan.get_customer(request.user.sm)
        if customer_id:
            params['customer_id'] = customer_id

        try:
            token = braintree.ClientToken.generate(params)
        except ValueError:
            token = braintree.ClientToken.generate()
        return Response({"token": token}, status=status.HTTP_201_CREATED)


class PromotionCodeView(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        """Check if the promotion code is correct or not

        Responses:

        200: {'discount_amount': 0.15}
        400: {'error': 'expire'}
        """
        try:
            code = promotion.validate_code(self.request.query_params.get('code', ''))
            data = dict(amount=code.amount)
            status = HTTP_200_OK
        except promotion.Error as e:
            data = dict(error=e.code)
            status = HTTP_400_BAD_REQUEST
        return Response(data, status=status)


class ResellerView(viewsets.ViewSet):
    serializer_class = serializers.ResellerSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwags):
        data = self.serializer_class(
            models.Customer.objects.filter(type=models.CustomerType.GAE_RESELLER), many=True).data
        return Response(data)


class ResellerRegisterView(viewsets.GenericViewSet, mixins.CreateModelMixin):
    parser_classes = (JSONParser, )
    renderer_classes = (JSONRenderer, )
    serializer_class = serializers.ResellerTempAccountSerializer
    queryset = models.ResellerTempAccount.objects
    permission_classes = []

    def perform_create(self, serializer):
        serializer.save(zoho_lead_id=create_tmp_lead(serializer))


class ResellerApproveView(View):
    # noinspection PyMethodMayBeStatic
    def post(self, request):
        lead_id = request.POST.get('lead_id')
        if lead_id is None:
            raise utils.BadRequestException('Lead ID is missing.')
        temp_record = get_object_or_404(models.ResellerTempAccount, zoho_lead_id=lead_id)
        with transaction.atomic():
            customer = models.Customer(
                name=temp_record.domain,
                org_name=temp_record.company,
                type='RESELLER',
                currency='USD',  # as default value
                registered=True,
            )
            customer.save()
            user = models.User(
                customer=customer,
                name=temp_record.first_name.strip() + ' ' + temp_record.last_name.strip(),
                # auth_user=None,
                email=temp_record.email,
                contact_email=temp_record.email,
                phone_number=temp_record.phone
            )
            user.save()
            convert_lead(user)
            temp_record.delete()


class OrderViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = models.Order.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_classes = {'list': serializers.OrderListSerializer, 'retrieve': serializers.RetrieveOrderSerializer}
    filter_class = filters.OrderFilterSet
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action)

    def get_queryset(self):
        query_set = super(OrderViewSet, self).get_queryset()
        user = self.request.user
        if hasattr(user, 'sm'):
            return query_set.filter(customer=self.request.user.sm.customer)
        else:
            raise utils.BadRequestException('Auth user was not provided')
