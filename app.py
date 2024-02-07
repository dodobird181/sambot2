from typing import Any, Dict, List

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    session,
    stream_with_context,
)

from bot import Sambot
from config import FLASK_SECRET_KEY
from conversation import Message
from templating import render_jinja2

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


@app.route("/stream")
def stream_html():

    user_content = request.args.get("user_content", None)
    if not user_content:
        return Response("missing required parameter: user_content", status=400)

    sambot = Sambot()
    session_convo = sambot.load_session_convo()

    def generate_html():
        for convo in sambot.stream_convo(user_content, session_convo):
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

    return Response(stream_with_context(generate_html()), mimetype="text/event-stream")


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
