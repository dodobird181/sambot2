from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    make_response,
    render_template,
    request,
    stream_with_context,
)

import bot
from config import FLASK_SECRET_KEY
from conversation import Message
from templating import render_jinja2

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


def validate_user_content():
    """
    Raise an error if user_content not in request. Otherwise return
    user_content.
    """
    if "user_content" not in request.args:
        abort(400, "missing required parameter: user_content")
    return request.args["user_content"]


def _stream_html_response(convo, user_content, stream_fn=bot.stream_convo):
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
            data = render_jinja2("convo.html", {"convo": convo})
            yield f"data: {data}\n\n"
    yield f"data: STOP\n\n"


@app.route("/stream")
def stream_sambot_response():
    session_convo = bot.load_session_convo()
    user_content = validate_user_content()
    return Response(
        response=stream_with_context(
            _stream_html_response(
                convo=session_convo,
                user_content=user_content,
            )
        ),
        mimetype="text/event-stream",
    )


@app.route("/stream_dummy")
def stream_dummy_response():
    session_convo = bot.load_session_convo()
    user_content = validate_user_content()
    return Response(
        response=stream_with_context(
            _stream_html_response(
                convo=session_convo,
                user_content=user_content,
                stream_fn=bot.dummy_stream,
            )
        ),
        mimetype="text/event-stream",
    )


@app.route("/stream_initial")
def stream_initial_response():
    session_convo = bot.load_session_convo()
    user_content = "THIS IS NOT A USER INPUT: Hey! Who are you?"
    return Response(
        response=stream_with_context(
            _stream_html_response(
                convo=session_convo,
                user_content=user_content,
                stream_fn=bot.stream_initial,
            )
        ),
        mimetype="text/event-stream",
    )


@app.route("/checkin", methods=["GET"])
def checkin():
    """
    Initial web-page check-in. Returns an existing convo, or creates a new one.
    """
    convo = bot.load_session_convo()
    html_content = render_jinja2("convo.html", {"convo": convo})
    response = make_response(html_content, 200)
    response.headers["Content-Type"] = "text/html"
    return response


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
