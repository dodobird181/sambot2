import flask
import settings
import models

app = flask.Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY


@app.route("/")
def home():
    messages = [models.Message(role='user', content='Hello world!')]
    pills = ['What\'s your work experience?', 'Can I see your resume?', 'Where did you grow up?']
    return flask.render_template("home.html", messages=messages, pills=pills)


if __name__ == "__main__":
    # For debugging only, not used in prod.
    app.run(debug=True)
