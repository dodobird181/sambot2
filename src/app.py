import flask
import settings
from models import Message, DisplayPills, Messages, BadId, NotFound, SystemMessage
from apis import openai as openai
import bleach
import time
from flask_wtf.csrf import CSRFProtect
import asyncio
import logger

_logger = logger.get_logger(__name__)


"""
TODO: Remove me once it's confirmed that async shit works on the frontend...
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Who won the world series in 2020?"}
]

print("sync stream = False...")
res1 = ai.get_completion(messages, 'gpt-3.5-turbo', stream=False)
print(res1)

print("async call...")
res_async = asyncio.run(ai.async_get_completion(messages, 'gpt-3.5-turbo'))
print(res_async)

print("sync stream = True...")
for t in ai.get_completion(messages, 'gpt-3.5-turbo', stream=True):
    print(f'sync token: {t}')

exit()
"""


app = flask.Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY
csrf = CSRFProtect(app)
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["SESSION_COOKIE_SECURE"] = True


def messages_gen_to_event_stream(messages_gen):
    """Convert a `Messages` generator to a server-side-event stream."""

    def html_gen():
        for messages in messages_gen:
            yield flask.render_template(
                "partial_messages.html", messages=messages.to_display()
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


def string_gen_to_messages_gen(string_gen, messages, user_content, system_message):
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
    generate_system_message_task = loop.create_task(system_message.generate())

    while not generate_system_message_task.done():
        old_msg = messages[len(messages) - 1]
        new_msg = Message(role="assistant", content=old_msg.content + ".")
        if new_msg.content == "....":
            new_msg.content = ""
        messages[len(messages) - 1] = new_msg
        yield messages
        loop.run_until_complete(asyncio.sleep(0.5))

    try:
        system_message = loop.run_until_complete(generate_system_message_task)
    except openai.APIConnectionError:
        # set fake system message and notify the user
        msg = 'Whoops! It looks like there\'s been an error connecting to the ChatGPT API. You can '
        msg += 'check https://status.openai.com/, or test your internet connection and try again!'
        string_gen = lambda _: (x for x in msg.split(' '))
        system_message = SystemMessage(messages, user_content, dummy=True)

    # Clean assistant message of any leftover '.'s
    messages[len(messages) - 1] = Message(role="assistant", content="")

    # Transform generated strings into messages
    for token in string_gen(messages):
        old_msg = messages[len(messages) - 1]
        new_msg = Message(role="assistant", content=old_msg.content + token + " ")
        messages[len(messages) - 1] = new_msg
        yield messages
    messages.save()


def debug_string_gen(messages):
    """Generate string tokens for debugging purposes."""
    debug_message = "Hello world! This is a dummy chat gpt response for sambot :)"
    for token in debug_message.split(" "):
        yield token
        time.sleep(0.1)


def openai_string_gen(messages):
    """Generate string tokens using openai's completions endpoint."""
    for token in openai.get_completion(
        messages=messages.to_gpt(),
        model="gpt-4o",
        stream=True,
    ):
        yield token


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


@app.route("/submit")
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
    _logger.error('RETURNING NORMAL MESSAGE')
    system_message = SystemMessage(messages, user_content, dummy=False)
    string_gen = debug_string_gen if settings.DEBUG else openai_string_gen
    return messages_gen_to_event_stream(
        string_gen_to_messages_gen(
            string_gen=string_gen,
            messages=messages,
            user_content=user_content,
            system_message=system_message,
        ),
    )


if __name__ == "__main__":
    # For debugging only, not used in prod.
    app.run(debug=True)
