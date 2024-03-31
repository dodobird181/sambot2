import flask

import settings

app = flask.Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY


@app.route("/")
def index():
    return "Hello world!"


if __name__ == "__main__":
    app.run(debug=True)
