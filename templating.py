"""
Module for rendering more complicated HTML templates using jinja2.
"""

from config import TEMPLATES_FILEPATH
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any


def render_jinja2(template_name: str, data: Dict[str, Any]) -> str:
    """
    Render an HTML template using jinja2 and return the HTML as a string.
    """
    env = Environment(loader=FileSystemLoader(TEMPLATES_FILEPATH))
    template = env.get_template(template_name)
    # remove newlines and tabs to clean up the HTML data
    return template.render(data).replace("\n", "").replace("\t", "")
