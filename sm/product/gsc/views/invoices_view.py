from weasyprint import HTML
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator

from sm.core.models import Order, OrderStatus
from sm.core.utils import CustomPaginator
from sm.product.gsc.views.decorator_view import profile_required
from sm.api.serializers import OrderListSerializer, RetrieveOrderSerializer
from sm.product.gsc.views.helpers import extend_context


class BaseInvoiceView(TemplateView):

    @method_decorator(profile_required)
    def dispatch(self, *args, **kwargs):
        return super(BaseInvoiceView, self).dispatch(*args, **kwargs)


class InvoiceListView(BaseInvoiceView):
    INVOICE_PER_PAGE = settings.INVOICE_PER_PAGE

    template_name = 'sm/product/gsc/invoices.html'

    def _get_paginator(self, customer):
        qs = Order.objects.filter(customer=customer).exclude(status=OrderStatus.CREATED).exclude(
            status=OrderStatus.DRAFT).order_by('-date')
        return CustomPaginator(qs, self.INVOICE_PER_PAGE)

    def get_context_data(self, **kwargs):
        context = super(InvoiceListView, self).get_context_data(**kwargs)
        paginator = self._get_paginator(self.request.user.sm.customer)
        orders = paginator.get_objects(self.request.GET.get('page'))
        context['invoices'] = OrderListSerializer(instance=orders, many=True).data
        context['page'] = orders
        return extend_context(context)


class InvoiceRetrieveView(BaseInvoiceView):
    content_type = 'application/pdf'
    template_name = 'sm/product/gsc/pdf_invoice.html'

    def _get_order(self, invoice_id):
        return get_object_or_404(Order, customer=self.request.user.sm.customer, id=invoice_id)

    def get_context_data(self, **kwargs):
        context = super(InvoiceRetrieveView, self).get_context_data(**kwargs)
        context['order'] = RetrieveOrderSerializer(instance=self._get_order(kwargs['invoice_id'])).data
        return extend_context(context)

    def render_to_response(self, context, **response_kwargs):
        pdf = HTML(string=render_to_string(self.template_name, context)).write_pdf()
        response = HttpResponse(pdf, content_type=self.content_type)
        response['Content-Disposition'] = 'inline; filename=invoice#{}.pdf'.format(context['order']['id'])
        response['Content-Transfer-Encoding'] = 'binary'
        return response
