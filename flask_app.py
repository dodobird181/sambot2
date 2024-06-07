import flask

import applogging
import models
import sambot
import status
import settings
import utils

app = flask.Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY
app.logger = applogging.get_logger(__name__)


@app.route("/")
def index_endpoint():
    """
    Client entry-point to the application.
    """
    return flask.render_template("index.html")


@app.route("/sambot")
def sambot_endpoint():
    """
    Endpoint for streaming sambot responses.
    """

    if "GET" != flask.request.method:
        # only GET requests are allowed
        app.logger.warning(f'Someone tried to hit the sambot endpoint with the following request: {flask.request.__dict__}')
        flask.abort(status.METHOD_NOT_ALLOWED)

    content = flask.request.args.get('content', None)
    chat = sambot.find_or_create_chat(flask.session)

    if not content:
        # GET request with no content fetches the user chat
        messages = [msg.dict() for msg in chat.messages]
        chat_html = utils.render_html("chat.html", messages=messages)
        return flask.Response(chat_html)

    # stream chat response for the user
    gen = sse_stream_chat_response(content, chat)
    stream = flask.stream_with_context(gen)
    return flask.Response(response=stream, mimetype="text/event-stream")


def sse_stream_chat_response(content, chat):
    """
    Choose a response strategy, resolve it, and stream back SSE-formatted chunks to the client.
    """

    # append user content to chat and yield
    chat.append_user(content)
    messages = [msg.dict() for msg in chat.messages]
    yield utils.render_html("chat.html", messages=messages)

    # signal the client to start ellipsis animation (it might take
    # some time before we start streaming an actual response...)
    yield "data: START ELLIPSIS\n\n"

    # stream back partially-updating chat objects as HTML
    #strategy = sambot.choose_response_strategy(content, chat)
    strategy = sambot.Strategy.DEFAULT
    for response_chat in sambot.resolve_response_strategy(content, chat, strategy):
        messages = [msg.dict() for msg in response_chat.messages]
        data = utils.render_html("chat.html", messages=messages)
        yield f"data: {data}\n\n"
    yield f"data: STOP\n\n"


if __name__ == "__main__":
    # For debugging only, not used in prod.
    app.run(debug=True)
