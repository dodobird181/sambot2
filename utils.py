import datetime as dt
import re

import logger


class LogTime:
    """
    Context manager that logs the amount of time spent executing the inner code.
    """

    def __init__(self, message: str, log_fn=logger.debug):
        self.message = message
        self.log_fn = log_fn
        self.start_time = None

    def __enter__(self):
        self.start_time = dt.datetime.now()

    def __exit__(self, exc_type, exc_val, exc_tb):
        seconds = (dt.datetime.now() - self.start_time).total_seconds()
        self.log_fn(self.message.format(seconds=seconds))


def log_dict(dikt, prefix="", log_fn=logger.debug):
    """
    Helper method for logging a dictionary.
    """
    for key, value in dikt.items():
        log_fn(f"{prefix}{key}: {value}")


def log_large_string(s: str, prefix="", line_length=80, delim=None, log_fn=logger.debug):
    """
    Logs a large string by splitting it into separate lines, each not exceeding
    the specified line length.

    :param s: The large string to be logged.
    :param line_length: The maximum length of each line.
    """
    if delim:
        for sub_s in s.split(delim):
            if sub_s:
                log_large_string(
                    s=f"{delim}{sub_s}",
                    prefix=prefix,
                    delim=None,
                    line_length=line_length,
                    log_fn=log_fn,
                )

    s = s.replace("\n", "")
    s = re.sub(r"\s+", " ", s)
    for i in range(0, len(s), line_length):
        log_fn(f"{prefix}{s[i : i + line_length]}")
