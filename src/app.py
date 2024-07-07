import flask
import settings
from models import Message, DisplayPills, Messages, BadId, NotFound, SystemMessage
from apis import openai as openai
import bleach
import time
from flask_wtf.csrf import CSRFProtect
import asyncio
import logger
import flask_limiter as fl

"""
TODO LIST:
1. CSS styling of webpage.
3. ratelimit submit endpoint
4. pip freeze requirements
5. deploy!
"""

"""
CSS changes:
1. left align
2. text size bigger
3. make my name in h1 the blue color
4. make input text box multiline wrap after text gets to a certain length
5. add disclaimer in light grey under the submit box.
6. change background color just like 1 value warmer (cream + yellowish tint)
7. add copyright samuel morris 2024.
8. add gh, linkedin, and email address copy to clipboard, and resume pdf opening icons
   underneath the disclaimer (dark grey color but mouse over it's blue like the rest of the page).
"""

_logger = logger.get_logger(__name__)

# create app
app = flask.Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY
csrf = CSRFProtect(app)
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["SESSION_COOKIE_SECURE"] = True


# create ratelimiter
limiter = fl.Limiter(
    fl.util.get_remote_address,
    app=app,
    default_limits=["360 per day"],
)


def messages_gen_to_event_stream(messages_gen):
    """Convert a `Messages` generator to a server-side-event stream."""

    def html_gen():
        for messages in messages_gen:
            yield flask.render_template(
                "messages.html", messages=messages.to_display()
            )

    def sse_gen():
        for html_data in html_gen():
            # Remove newlines and carriage returns that interfere with streaming
            formatted_html = html_data.replace("\n", " ").replace("\r", " ")
            yield f"data: {formatted_html}\n\n"
        yield "data: STOP\n\n"  # Signal end of stream

    return flask.Response(
        flask.stream_with_context(sse_gen()), mimetype="text/event-stream"
    )


def string_gen_to_messages_gen(string_gen, messages, user_content, system_message_content):
    """
    Convert a string generator into a `Messages` generator using the given `Messages` object.
    NOTE: side-effects include mutating the `Messages` object, saving the `Messages` object, and
          computing the system message.
    NOTE: This method is not a 1:1 conversion between a string generator and a messages generator.
          The system message can take significant time to compute, so an ellipsis animation is streamed
          back to the client while this occurrs.
    """

    # Append user content to messages and add empty assistant message
    messages.append(Message(role="user", content=user_content))
    messages.append(Message(role="assistant", content=""))

    # Generate system message and stream ellipsis
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    generate_system_message_task = loop.create_task(system_message_content.generate())

    while not generate_system_message_task.done():
        old_msg = messages[len(messages) - 1]
        new_msg = Message(role="assistant", content=old_msg.content + ".")
        if new_msg.content == "....":
            new_msg.content = ""
        messages[len(messages) - 1] = new_msg
        yield messages
        loop.run_until_complete(asyncio.sleep(0.5))

    try:
        system_message_content = loop.run_until_complete(generate_system_message_task)
    except openai.APIConnectionError:
        # set fake system message and notify the user
        # NOTE: This is kind of a hack because technically this call could succeed but
        #       the next call to openai could fail to connect and this message wouldn't show up...
        string_gen = connection_error_string_gen
        system_message_content = SystemMessage(messages, user_content, dummy=True)

    # set system message
    messages[0] = Message(role='system', content=system_message_content)

    # Clean assistant message of any leftover '.'s
    messages[len(messages) - 1] = Message(role="assistant", content="")

    # Transform generated strings into messages
    for token in string_gen(messages):
        old_msg = messages[len(messages) - 1]
        new_msg = Message(role="assistant", content=old_msg.content + token)
        messages[len(messages) - 1] = new_msg
        yield messages
    messages.save()


def debug_string_gen(messages):
    """Generate string tokens for debugging purposes."""
    debug_message = "Hello world! This is a dummy chat gpt response for sambot :)"
    for token in debug_message.split(" "):
        yield token + " "
        time.sleep(0.1)


def openai_string_gen(messages):
    """Generate string tokens using openai's completions endpoint."""
    for token in openai.get_completion(
        messages=messages.to_gpt(),
        model="gpt-4o",
        stream=True,
        temperature=0.15,
    ):
        yield token


def connection_error_string_gen(message):
    """Generate string tokens for when a connection error occurrs."""
    connection_error_message = 'Whoops! It looks like there\'s been an error connecting to '
    connection_error_message += 'the ChatGPT API. You can check https://status.openai.com/, '
    connection_error_message += 'or test your internet connection and try again!'
    for token in connection_error_message.split(' '):
        yield token + " "
        time.sleep(0.1)


def ratelimit_string_gen(message):
    """Generate string tokens for when the client gets ratelimited on the submit endpoint."""
    ratelimit_error_message = 'Woah there! You\'ve hit the limit for submissions. Please try again in a bit.'
    for token in ratelimit_error_message.split(' '):
        yield token + " "
        time.sleep(0.1)


@app.route("/")
def home():

    # Get current messages from session (or create a new one)
    try:
        id = flask.session.get(settings.SESSION_MESSAGES_KEY, None)
        messages = Messages.load_from_id(id)
    except BadId:
        messages = Messages.create(system="")  #  System message gets populated by SystemMessage object later
    flask.session[settings.SESSION_MESSAGES_KEY] = str(messages.id)

    # Generate suggestion pills
    pills = DisplayPills(messages)
    pills.generate()

    # Render homepage
    return flask.render_template(
        template_name_or_list="home.html",
        messages=messages.to_display(),
        pills=pills,
    )

# TODO: Ratelimit this silly willy
@app.route("/submit")
@limiter.limit("8 per minute")
def submit():

    # Get user submission (or raise)
    user_content = flask.request.args.get("user_content", None)
    user_content = bleach.clean(user_content, strip=True)
    if not user_content:
        flask.abort(400)

    # Get messages from flask session (or raise)
    try:
        messages_id = flask.session.get(settings.SESSION_MESSAGES_KEY, None)
        messages = Messages.load_from_id(messages_id)
    except BadId:
        flask.abort(404)

    # Stream back data to the client
    system_message = SystemMessage(messages, user_content)
    string_gen = debug_string_gen if settings.DEBUG else openai_string_gen
    return messages_gen_to_event_stream(
        string_gen_to_messages_gen(
            string_gen=string_gen,
            messages=messages,
            user_content=user_content,
            system_message_content=system_message,
        ),
    )


@app.route('/resume')
@limiter.limit("50 per hour")
def resume():
    return flask.send_from_directory('static', 'resume.pdf')


@app.errorhandler(fl.RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    if flask.request.endpoint == 'submit':
        user_content = flask.request.args.get('user_content', None)

        # Get messages from flask session (or raise)
        try:
            messages_id = flask.session.get(settings.SESSION_MESSAGES_KEY, None)
            messages = Messages.load_from_id(messages_id)
        except BadId:
            flask.abort(404)

        # stream back ratelimit message on submit
        system_message = SystemMessage(messages, user_content, dummy=True)
        return messages_gen_to_event_stream(
            string_gen_to_messages_gen(
                string_gen=ratelimit_string_gen,
                messages=messages,
                user_content=user_content,
                system_message_content=system_message,
            ),
        )

    # all other endpoints return 429 TOO_MANY_REQUESTS
    flask.abort(429)


if __name__ == "__main__":
    # For debugging only, not used in prod.
    app.run(debug=True)
