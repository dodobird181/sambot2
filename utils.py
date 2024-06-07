import uuid

import flask
import jinja2

import settings


class Factory:
    """
    Base factory class for database objects.
    """

    @staticmethod
    def path(obj_or_id) -> str:
        """
        Get the database path for a given object, or it's uuid if known.
        """
        id = obj_or_id if isinstance(obj_or_id, (str, uuid.UUID)) else obj_or_id.id
        return f"{settings.PICKLE_DB_PATH}{id}.pkl"


def render_html(name, **data):
    """
    Render an HTML template using jinja2 and return the HTML as a string.
    """
    loader = jinja2.FileSystemLoader(settings.TEMPLATES_FILEPATH)
    env = jinja2.Environment(loader=loader)
    template = env.get_template(name)
    # remove newlines and tabs to clean up the HTML data
    return template.render(data).replace("\n", "").replace("\t", "")
