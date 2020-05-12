try:
    import socket, os

    os.environ.setdefault('PG_HOST', socket.gethostbyname('sm-services'))
    os.environ.setdefault('REDIS_HOST', socket.gethostbyname('sm-services'))
except:
    pass

from app.sharing_settings import *
