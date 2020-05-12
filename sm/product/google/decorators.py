import time
import logging


def log_time(func):
    logger = logging.getLogger("{}.{}".format(func.__module__, func.__name__))

    def wrapper(*args, **kwargs):
        ts = time.time()
        result = func(*args, **kwargs)
        te = time.time()
        logger.info('time taken %2.2f ms' % ((te - ts) * 1000))
        return result

    return wrapper
