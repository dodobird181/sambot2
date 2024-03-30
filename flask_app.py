import flask
import config


app = flask.Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

@app.route("/")
def index():
    return flask.render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
