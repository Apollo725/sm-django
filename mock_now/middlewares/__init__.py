from django.templatetags.static import static
from django.conf import settings
from django.utils import timezone
import datetime
from django.core.urlresolvers import reverse


class MockNowMiddleware(object):
    def process_response(self, request, response):
        if settings.DEBUG:
            if 'content-type' not in response:
                return response
            if ('html' in response['content-type'] and
                    len(response.content) > 0 and '</head>' in response.content):
                now = timezone.now()
                timestamp = (now - datetime.datetime(1970, 1, 1, tzinfo=now.tzinfo)).total_seconds()
                url = str(reverse('mock_now:mock_now'))

                response.content = \
                    response.content.replace('</head>',
                                             '<script src="%s" id="mock-now" data-mockNow-timestamp="%s"'
                                             ' data-mockNow-url="%s"></script></head>' %
                                             (
                                                 static(
                                                     'mock_now/js/mock_now.js'),
                                                 timestamp,
                                                 url
                                             )
                                             )

        return response
