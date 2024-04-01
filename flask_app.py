import flask

import settings

app = flask.Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY


@app.route("/")
def index():
    return flask.render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
