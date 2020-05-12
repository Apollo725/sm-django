from __future__ import absolute_import

from django.test import TestCase, override_settings
from mock_now import core as mock_now
import mock
from mock_now.signals import post_now_mocked


class TestMockNow(TestCase):

    @override_settings(
        DEBUG=True,
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
            }
        }
    )
    def test_mock_now(self):
        time_mocked = mock.MagicMock()
        post_now_mocked.connect(time_mocked)

        from django.utils import timezone
        from datetime import timedelta
        time_now = timezone.now()
        delta = timedelta(seconds=30)
        mock_now.set_mock_now(time_now + delta)
        time_now_2 = timezone.now()
        _, kwargs = time_mocked.call_args
        self.assertEquals(30, round((time_now_2 - time_now).total_seconds()))
        self.assertEquals(30, kwargs['offset'])

    @override_settings(
        DEBUG=False,
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
            }
        }
    )
    def test_mock_now_2(self):
        from django.utils.timezone import now
        from datetime import timedelta
        time_now = now()
        delta = timedelta(seconds=30)
        mock_now.set_mock_now(time_now + delta)
        time_now_2 = now()
        self.assertEquals(0, round((time_now_2 - time_now).total_seconds()))
