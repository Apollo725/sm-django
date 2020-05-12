from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from sm.core.models import (Catalog, DefaultProductPlan, OrderType,
                            ProductCategory, ProductPlan, SubscriptionPlan,
                            VendorStatus)
from sm.core.utils.model_utils import get_user_subscriptions
from sm.new_frontend.authenticate import HasProfile

from .serializers import PricingPlansSerializer


class ListPricingPlansView(ListAPIView):
    permission_classes = (IsAuthenticated, HasProfile)

    def get(self, request):
        product_category = get_object_or_404(
            ProductCategory,
            id=request.GET.get('product_category_id')
        )
        user_subscriptions = get_user_subscriptions(request.user.sm.customer) \
            .filter(product__category=product_category)
        latest_user_subscription = user_subscriptions.first()
        if latest_user_subscription is not None:
            current_product = latest_user_subscription.product
            catalog = latest_user_subscription.catalog
        else:
            current_product = product_category.default_product
            catalog = Catalog.objects.get(default=True)

        if not user_subscriptions:
            action = OrderType.NEW
        else:
            is_subscriptions_paid = user_subscriptions.filter(
                vendor_status__in=[VendorStatus.PAID,
                                   VendorStatus.UNINSTALLED_PAID]
            ).exists()
            if is_subscriptions_paid:
                action = OrderType.UPGRADE
            else:
                action = OrderType.NEW

        default_plan_id = None
        if action == OrderType.NEW and latest_user_subscription is not None:
            default_plan = DefaultProductPlan.objects \
                .filter(
                    current_product=latest_user_subscription.product,
                    users_limit__gte=latest_user_subscription.billable_licenses
                ).first()
            default_plan_id = default_plan and default_plan.id or None
        elif action == OrderType.UPGRADE and latest_user_subscription is not None:
            default_plan_id = latest_user_subscription.product.plan.id
        if default_plan_id is None:
            default_plan_id = ProductPlan.objects.get(
                codename=SubscriptionPlan.ANNUAL_YEARLY.value
            ).id
        response_data = PricingPlansSerializer(
            many=False,
            instance=product_category,
            context={
                'default_plan_id': default_plan_id,
                'catalog': catalog,
                'current_product': current_product,
                'action_type': action.value,
            }
        ).data
        response_data['order_type'] = action.value

        return Response(response_data)
