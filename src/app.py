import flask
import settings
from models import Message, DisplayPills, Messages, BadId, NotFound, SystemMessage
from apis import openai as openai
import time
import bleach
import html
import re
from flask_wtf.csrf import CSRFProtect

app = flask.Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY
csrf = CSRFProtect(app)
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_SECURE'] = True


def html_gen_to_event_stream(html_gen):
    """Convert an HTML generator to a server-side-event stream."""
    def sse_gen():
        for html_data in html_gen:
            # remove newlines and carrige returns that interfer with streaming
            formatted_html = html_data.replace('\n', ' ').replace('\r', ' ')
            yield f"data: {formatted_html}\n\n"
        yield f"data: STOP\n\n"
    return flask.stream_with_context(sse_gen())


def messages_gen_to_html_gen(messages_gen):
    """Convert a `Messages` generator to an HTML generator representing those `Messages`."""
    for messages in messages_gen:
        yield flask.render_template('partial_messages.html', messages=messages)


@app.route("/")
def home():


    # get current messages from session (or create a new one)
    try:
        id = flask.session.get(settings.SESSION_MESSAGES_KEY, None)
        messages = Messages.load_from_id(id)
    except BadId:
        messages = Messages.create('TODO: DUMMY SYSTEM MESSAGE')
    flask.session[settings.SESSION_MESSAGES_KEY] = str(messages.id)

    # generate suggestion pills
    pills = DisplayPills(messages)
    pills.generate()

    # render homepage
    return flask.render_template("home.html", messages=messages.to_display(), pills=pills)


@app.route("/submit")
def submit():

    # get user submission (or raise)
    user_content = flask.request.args.get('user_content', None)
    user_content = bleach.clean(user_content, strip=True)
    if not user_content:
        flask.abort(400)

    # generate a system message
    messages_id = flask.session.get(settings.SESSION_MESSAGES_KEY, None)
    messages = Messages.load_from_id(messages_id)
    system = SystemMessage(messages, user_content)
    system = system.generate()

    # define messages stream
    def html_messages_gen(dummy=settings.DEBUG):
        messages.append(Message(role='user', content=user_content))
        messages.append(Message(role='assistant', content=''))

        if dummy:
            for token in 'Hello world! This is a dummy chat gpt response for sambot :)'.split(' '):
                old_msg = messages[len(messages) - 1]
                new_msg = Message(role='assistant', content=old_msg.content + token + ' ')
                messages[len(messages) - 1] = new_msg
                yield flask.render_template('partial_messages.html', messages=messages)
                time.sleep(0.1)
            messages.save()
            return  # prevent real code from executing

        # real api call
        for token in openai.get_completion(messages=messages.to_gpt(), model='gpt-4o', stream=True):
            old_msg = messages[len(messages) - 1]
            new_msg = Message(role='assistant', content=old_msg.content + token)
            messages[len(messages) - 1] = new_msg
            yield flask.render_template('partial_messages.html', messages=messages)
        messages.save()

    # return flask SSE stream
    return flask.Response(response=html_gen_to_event_stream(html_messages_gen()), mimetype="text/event-stream")

if __name__ == "__main__":
    # For debugging only, not used in prod.
    app.run(debug=True)
