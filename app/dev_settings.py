from app.sharing_settings import *

try:
    from .local_settings import *
except ImportError as e:
    print("Local setting load error: {}".format(e))
