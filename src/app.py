import flask
import settings
from models import Message, Messages, DisplayPills

app = flask.Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY


@app.route("/")
def home():
    messages = Messages.create(system='You are a helpful assistant')
    messages.append(Message(role='user', content='hello world!'))
    messages.append(Message(role='assistant', content='hello right back at ya!'))
    messages.save()
    pills = DisplayPills(messages, dummy=True)
    pills.generate()
    return flask.render_template("home.html", messages=messages.to_display(), pills=pills)


if __name__ == "__main__":
    # For debugging only, not used in prod.
    app.run(debug=True)
