"""Module for loading data in the res folder."""

import logger
import settings

_logger = logger.get_logger(__name__)


def _read(path_inside_res) -> str:
    path = f'{settings.LOCAL_RESOURCE_DIR}/{path_inside_res}'
    try:
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError as e:
        _logger.error(f"Failed to load resource file: {e}.")


STYLE = _read("style.md")
INFO = _read("info.md")
STARTERS = _read("starters.md")
