import logging
import sys

import settings

GREEN_LOGGING_LEVEL = 60  # Higher than critical.
logging.addLevelName(GREEN_LOGGING_LEVEL, "GREEN")

BLUE_LOGGING_LEVEL = 61  # Higher than critical
logging.addLevelName(BLUE_LOGGING_LEVEL, "BLUE")


class CustomLogger(logging.Logger):
    """
    Custom logger!
    """

    def green(self, message, *args, **kwargs):
        if self.isEnabledFor(GREEN_LOGGING_LEVEL):
            self._log(GREEN_LOGGING_LEVEL, message, args, **kwargs)

    def blue(self, message, *args, **kwargs):
        if self.isEnabledFor(BLUE_LOGGING_LEVEL):
            self._log(BLUE_LOGGING_LEVEL, message, args, **kwargs)


class ColorFormatter(logging.Formatter):
    """
    Logging formatter that adds a nice datetime format and colors.
    """

    blue = "\033[94m"
    green = "\033[92m"
    grey = "\x1b[38;21m"
    dark_grey = "\x1b[38;5;235m"
    yellow = "\x1b[33;21m"
    bold_red = "\x1b[31;21m"
    red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: dark_grey + format_str + reset,
        logging.INFO: grey + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset,
        GREEN_LOGGING_LEVEL: green + format_str + reset,
        BLUE_LOGGING_LEVEL: blue + format_str + reset,
    }

    def format(self, record):
        formatter = logging.Formatter(
            fmt=self.FORMATS.get(record.levelno),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        return formatter.format(record)


def get_logger(name):
    """
    Get a new logger instance with the given module name.
    """
    logger = CustomLogger(name)
    logger.setLevel(settings.LOGGING_LEVEL)
    handler = logging.StreamHandler()
    formatter = ColorFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
