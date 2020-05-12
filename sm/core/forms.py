from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import ugettext as _

from .models import Product


class SelectProducts(forms.Form):
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.all(),
        label=_('Select products to copy options'),
        widget=FilteredSelectMultiple(verbose_name=_('products'), is_stacked=False),
    )
