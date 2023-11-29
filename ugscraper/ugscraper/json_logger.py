import json
from scrapy.logformatter import LogFormatter
import logging
import os


class JsonLogFormatter(LogFormatter):
    def crawled(self, item, exception, response):
        return {
            "level": logging.INFO,  # lowering the level from logging.WARNING
            "msg": "Dropped: %(exception)s" + os.linesep + "%(item)s",
            "args": {
                "exception": exception,
                "item": item,
            },
        }
