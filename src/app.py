import flask
import settings
from models import Message, DisplayPills, Messages, BadId, NotFound, SystemMessage
from apis import openai as openai
import time
import bleach
from flask_wtf.csrf import CSRFProtect

app = flask.Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY
csrf = CSRFProtect(app)
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_SECURE'] = True


def html_gen_to_event_stream(html_gen):
    """Helper method that converts an HTML generator to a server-side-event stream."""
    def sse_gen():
        for html_data in html_gen:
            yield f"data: {html_data}\n\n"
        yield f"data: STOP\n\n"
    return flask.stream_with_context(sse_gen())


app.route("/")
def home():

    # get current messages from session (or create a new one)
    try:
        id = flask.session.get(settings.SESSION_MESSAGES_KEY, None)
        messages = Messages.load_from_id(id)
    except BadId:
        messages = Messages.create('TODO: DUMMY SYSTEM MESSAGE')
    flask.session[settings.SESSION_MESSAGES_KEY] = str(messages.id)

    # generate suggestion pills
    pills = DisplayPills(messages, dummy=True)
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
    system = SystemMessage(messages, user_content, dummy=True)
    system = system.generate()

    # define messages stream
    def html_messages_gen(dummy=False):
        messages.append(Message(role='user', content=user_content))
        messages.append(Message(role='assistant', content=''))
        if dummy:
            for token in 'Hello world! This is a dummy chat gpt response for sambot :)':
                old_msg = messages[len(messages) - 1]
                new_msg = Message(role='assistant', content=old_msg.content + token)
                messages[len(messages) - 1] = new_msg
                yield flask.render_template('partial_messages.html', messages=messages)
                time.sleep(0.2)
            return  # prevent real code from executing

        # real api call
        for token in openai.get_completion(messages=messages.to_gpt(), model='gpt-4o', stream=True):
            old_msg = messages[len(messages) - 1]
            new_msg = Message(role='assistant', content=old_msg.content + token)
            messages[len(messages) - 1] = new_msg
            yield flask.render_template('partial_messages.html', messages=messages)

    # TODO: return flask stream event mime type
    return flask.Response(response=html_gen_to_event_stream(html_messages_gen()), mimetype="text/event-stream")

if __name__ == "__main__":
    # For debugging only, not used in prod.
    app.run(debug=True)
