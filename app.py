from flask import (
    Flask,
    request,
    session,
    jsonify,
    Response,
    stream_with_context,
    render_template,

            )
from templating import render_jinja2
from conversation import Message
from config import FLASK_SECRET_KEY
from typing import Any, List, Dict

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


@app.route("/stream")
def stream_html():
    def generate_html():
        from conversation import Conversation, SystemMessage, UserMessage, BotMessage
        from gpt import chat_stream

        convo = Conversation(SystemMessage("You are a helpful assistant named Dave."))
        convo.append(UserMessage(user_content))
        convo.append(BotMessage(""))
        partial_response = ""
        for token in chat_stream(convo=convo):
            partial_response += token
            convo.update(
                BotMessage(
                    partial_response.replace("\n", " ").replace("\t", " ").lower()
                )
            )
            data = render_jinja2("convo.html", {"convo": convo})
            yield f"data: {data}\n\n"
        yield f"data: STOP\n\n"

    return Response(stream_with_context(generate_html()), mimetype="text/event-stream")


"""
@app.route('/stream')
def stream_html():
    def generate_html():
        from conversation import Conversation, SystemMessage, UserMessage, BotMessage
        from gpt import chat_stream
        user_content = request.args.get('user_content', default=None, type=str)
        if not user_content:
            return 400, 'user_content required'
        convo = Conversation(SystemMessage('You are a helpful assistant named Dave.'))
        convo.append(UserMessage(user_content))
        convo.append(BotMessage(''))
        partial_response = ''
        for token in chat_stream(convo=convo):
            partial_response += token
            convo.update(BotMessage(partial_response.replace("\n", " ").replace("\t", " ").lower()))
            data = render_jinja2('convo.html', {'convo': convo})
            yield f'data: {data}\n\n'
        yield f'data: STOP\n\n'

    return Response(stream_with_context(generate_html()), mimetype='text/event-stream')
"""


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
