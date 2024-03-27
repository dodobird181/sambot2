import logging
import sys

import config

# TODO: colored logging?


def _create_logger(name=__name__) -> logging.Logger:
    """
    Create a logger instance.
    """
    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(config.LOGGING_LEVEL)
    handler.setFormatter(formatter)

    logger = logging.Logger(name)
    logger.setLevel(config.LOGGING_LEVEL)
    logger.addHandler(handler)
    return logger


_logger = _create_logger()

info = _logger.info
debug = _logger.debug
warning = _logger.warning
error = _logger.error
