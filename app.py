from flask import Flask, request, jsonify, Response, stream_with_context, render_template
import time
from templating import render_jinja2
from conversation import Message

app = Flask(__name__)


@app.route('/stream')
def stream_html():
    def generate_html():
        from conversation import Conversation, SystemMessage, UserMessage, BotMessage
        from gpt import chat_stream
        user_content = request.args.get('user_content', default=None, type=str)
        if not user_content:
            return 400, 'user_content required'
        convo = Conversation(SystemMessage('You are a helpful assistant named Dave.'))
        """for i in range(1, 6):
            # yield f"data: <div><h3>Chunk {i} of HTML content</h3></div>\n\n"
            if isinstance(convo.latest, (BotMessage, SystemMessage)):
                convo.append(UserMessage(f'User message {i}'))
            else:
                convo.append(BotMessage(f'Bot message {i}'))
            data = render_jinja2('convo.html', {'convo': convo})
            print(data)
            yield f"data: {data}\n\n"
            time.sleep(1)  # Simulate delay
        yield f'data: STOP\n\n'
        """
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


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)