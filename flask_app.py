import flask

import settings
import utils

from . import Chat

app = flask.Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY


@app.route("/")
def index():
    """
    Client entry-point to the application.
    """
    return flask.render_template("index.html")


@app.route("/sambot")
def sambot():
    """
    Endpoint for streaming sambot responses.
    """

    # retrieve the current chat, or make a new one
    content = utils.get_or_400("content")
    _chat_id = flask.session.get(settings.SESSION_CHAT_KEY)
    session_chat = Chat.objects.find_or_create(_chat_id)
    flask.session[settings.SESSION_CHAT_KEY] = session_chat.id

    # stream response


if __name__ == "__main__":
    # For debugging only, not used in prod.
    app.run(debug=True)
