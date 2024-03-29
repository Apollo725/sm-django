from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test

__author__ = 'hoozecn'


def test_auth_function(user):
    return user.is_authenticated() and getattr(user, 'sm', None)


def login_required(function=None,
                   redirect_field_name=REDIRECT_FIELD_NAME,
                   login_url=None,
                   test_auth_func=test_auth_function):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        test_auth_func,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
