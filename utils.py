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


def get_or_400(query_param):
    """
    Get the given query_param from the request session, or
    raise a 400_BAD_REQUEST if the parameter could not be found.
    """
    try:
        return flask.request.args[query_param]
    except KeyError:
        flask.abort(400, f'Missing required parameter "{query_param}".')


def stream_chat_response_to_html(chat, user_content, stream_fn=bot.stream_convo):
    """
    Repeatedly yield the entire conversation as HTML data, as the bot message is
    updated by the stream.
    """
    for convo in stream_fn(user_content, convo):
        if isinstance(convo, str):
            # pass-along arbitrary string as data for the client to interpret.
            # this allows stream_convo to send intermediate messages to the
            # client while the main data is also being streamed...
            yield f"data: {convo}\n\n"
        else:
            # render convo to HTML and yield partial result
            data = render_html("chat.html", convo=convo)
            yield f"data: {data}\n\n"
    yield f"data: STOP\n\n"
