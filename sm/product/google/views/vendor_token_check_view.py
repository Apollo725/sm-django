import logging

from django.http import JsonResponse

from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from djangorestframework_camel_case.parser import CamelCaseJSONParser

from sm.new_frontend.authenticate import HasProfile
from sm.product.google.serializers.vendor_token_serializer \
    import VendorTokenSerializer, ProcessingException
from sm.product.google.decorators import log_time


logger = logging.getLogger(__name__)


class VendorTokenCheckView(CreateAPIView):
    serializer_class = VendorTokenSerializer
    parser_classes = [CamelCaseJSONParser]
    permission_classes = (IsAuthenticated, HasProfile)

    def get_serializer(self, request, *args, **kwargs):
        customer_id = request.user.sm.customer_id
        if request and request.data:
            context = request.data
            context['customer'] = customer_id
        return super(VendorTokenCheckView, self).get_serializer(data=context)

    @log_time
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(request, *args, **kwargs)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)

            eligible_json = {
                'eligible': True,
            }
            return JsonResponse(eligible_json)
        except ProcessingException as e:
            eligible_json = {
                'eligible': False,
                'error': True,
                'reason': e.default_detail
            }
            return JsonResponse(eligible_json)
