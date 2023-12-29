import sys
import logging

WHITE = '\033[97m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET_COLOR = '\033[0m'

FORMAT_DICT = {
    logging.DEBUG: WHITE + "%(message)s" + RESET_COLOR,
    logging.INFO: WHITE + "%(message)s" + RESET_COLOR,
    logging.WARNING: YELLOW + "%(message)s" + RESET_COLOR,
    logging.ERROR: RED + "%(message)s" + RESET_COLOR,
    logging.CRITICAL: RED + "%(message)s" + RESET_COLOR,
}

def format_with_color(record):
    color_format = FORMAT_DICT[record.levelno]
    formatter = logging.Formatter(color_format)
    return formatter.format(record)

formatter = logging.Formatter()
formatter.format = format_with_color

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

self = sys.modules[__name__]
setattr(self, 'debug', logger.debug)
setattr(self, 'warning', logger.warning)
setattr(self, 'error', logger.error)