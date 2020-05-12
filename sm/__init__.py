import logging.handlers

class FileHandler(logging.handlers.TimedRotatingFileHandler):
    def __init__(self, **kwargs):
        super(FileHandler, self).__init__(kwargs)


