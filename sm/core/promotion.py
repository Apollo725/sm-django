from __future__ import absolute_import
import datetime
from django.utils import timezone
from .models import DiscountCode


class Error(Exception):
    def __init__(self, message, code, *args, **kwargs):
        super(Error, self).__init__(message, *args, **kwargs)
        self.code = code

    def __str__(self):
        return "{}: {}".format(self.code, self.message)


def validate_code(pr):
    """Validate the input promotion code

    :rtype: DiscountCode
    :type pr: basestring
    :raise Error
    """
    assert isinstance(pr, (str, unicode))

    if not pr or len(pr) != 13:
        raise Error("length of promotion code is not 13", code='length_error')
    promotion = pr[:1] + pr[3:5] + pr[6:7] + pr[8:9] + pr[10:11] + pr[12:]
    date = pr[1:3] + pr[5:6] + pr[7:8] + pr[9:10] + pr[11:12]
    try:
        date = datetime.datetime.strptime(date, '%d%y%m').replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise Error("invalid datetime found in promotion code %s" % e, 'invalid_date')

    if date < timezone.now():
        raise Error("promotion code is expired", 'expired')

    code = DiscountCode.objects.filter(code=promotion).first()
    if code:
        assert isinstance(code, DiscountCode)
        if code.end_at and code.end_at < timezone.now():
            raise Error("promotion code is ended", 'ended')
        return code
    raise Error("promotion code is not found", 'not_found')
