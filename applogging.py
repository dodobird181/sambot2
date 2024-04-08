import logging
import time

import settings

GREEN_LOGGING_LEVEL = 60  # Higher than critical.
logging.addLevelName(GREEN_LOGGING_LEVEL, "GREEN")

BLUE_LOGGING_LEVEL = 61  # Higher than critical
logging.addLevelName(BLUE_LOGGING_LEVEL, "BLUE")


class LogTimeContextManager:
    """
    Context manager that logs the elapsed time it takes to perform an operation.
    """

    def __init__(self, start_end_end_message, log_fn):
        """
        The `start_end_end_message` is the message that will be displayed
        on enter and exit of the context manager. The `log_fn` is the function
        that will be used to log both these messages.
        """
        self.message = start_end_end_message
        self.log_fn = log_fn

    def __enter__(self):
        """
        Save start time and log.
        """
        self.start_time = time.time()
        self.log_fn(f"{self.message.capitalize()}...")

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Compute end time and log.
        """
        self.elapsed_time = time.time() - self.start_time
        self.log_fn(f"Finished {self.message.lower()} in {self.elapsed_time:.2f} seconds.")
        # Return False to propagate the exception, if any occurred
        return False


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

    def logtime(self, start_and_end_message, log_fn=None, *args, **kwargs):
        """
        Measure how much time has elapsed during the execution of
        the inner function and log this value along with the start_and_end_message.
        """
        log_fn = self.debug if not log_fn else log_fn
        return LogTimeContextManager(start_and_end_message, log_fn)


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
