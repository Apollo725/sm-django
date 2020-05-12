"""
Functions to mock now function
"""
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta
from django.utils.timezone import now
from mock_now import signals
import sys
import logging

logger = logging.getLogger('mock_now.core')

real_now = now
seconds_of_day = 3600 * 24

MOCK_NOW_CACHE_KEY = getattr(
    settings, 'MOCK_NOW_CACHE_KEY', 'mock_now_cache_key')


def monkey_patch():
    import django.utils.timezone
    django.utils.timezone.now = _mock_now


def set_mock_now(mock_datetime):
    offset = int(round((mock_datetime - real_now()).total_seconds()))
    _set_offset(offset)
    signals.post_now_mocked.send(
        sender=sys.modules['mock_now'],
        offset=offset,
        new_time=mock_datetime
    )


def _mock_now():
    if settings.DEBUG:
        offset = _get_offset()
        return real_now() + timedelta(
            days=int(offset / seconds_of_day),
            seconds=int(offset % (seconds_of_day)))
    else:
        return real_now()


def _get_offset():
    offset = cache.get(MOCK_NOW_CACHE_KEY)
    if not offset:
        return 0
    else:
        return int(offset)


def _set_offset(offset):
    # expires in 10 years
    cache.set(MOCK_NOW_CACHE_KEY, str(offset), 10 * 365 * 24 * 3600)
