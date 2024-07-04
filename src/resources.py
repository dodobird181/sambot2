"""Module for loading data in the res folder."""

import logger

_logger = logger.get_logger(__name__)


def _read(path_inside_res) -> str:
    path = f'../res/{path_inside_res}'
    try:
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError as e:
        _logger.error(f"Failed to load resource file: {e}.")


STYLE = _read("style.md")
INFO = _read("info.md")
DEFAULT_SYS_MSG = _read("default_sys_msg.md")
