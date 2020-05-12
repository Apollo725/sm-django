from django.dispatch import Signal

post_now_mocked = Signal(providing_args=['offset', 'new_datetime'])
