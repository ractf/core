# type: ignore[attr-defined]
# This is to work around Python Magic and is bad practice

import logging
from datetime import datetime

class ParseRequestLog(logging.Filter):
    def filter(self, record):
        record.path = record.request.path
        record.remote_ip = record.request.META["REMOTE_ADDR"] # TODO
        record.time = datetime.now()
        del record.request
        record.level = record.levelname
        # TODO: Get user details
        return True
