import flask
import settings

app = flask.Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY


@app.route("/")
def home():
    return flask.render_template("home.html", messages=[
        {
            'role': 'assistant',
            'content': 'hello world!',
        },
    ])


if __name__ == "__main__":
    # For debugging only, not used in prod.
    app.run(debug=True)
