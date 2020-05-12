from __future__ import absolute_import


def request2context(request):
    from django.conf import settings
    if settings.DEBUG:
        context = {}
        for key in request.GET:
            context[key] = request.GET[key]
        return context
    return {}
