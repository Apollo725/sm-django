import django_filters
from rest_framework.exceptions import ValidationError

from sm.core.models import Order


class SeparatorFilter(django_filters.Filter):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('lookup_expr', 'in')
        self.separator = kwargs.pop('separator', ',')
        super(SeparatorFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        values = value.split(self.separator) if value else ()
        try:
            return super(SeparatorFilter, self).filter(qs, values)
        except ValueError:
            raise ValidationError(
                'Invalid value for "{}" parameter: {}'.format(self.name, value))


class OrderFilterSet(django_filters.FilterSet):

    status = SeparatorFilter()
    status_exclude = SeparatorFilter(name='status', exclude=True)

    class Meta:
        model = Order
        fields = ('status', 'status_exclude')
