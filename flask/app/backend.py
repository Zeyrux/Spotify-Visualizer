import os
import secrets

from app.SpotifyAPI import SpotifyAPI, TokenManager
# from SpotifyAPI import SpotifyAPI, TokenManager

from flask import (
    Flask,
    request,
    session,
    render_template,
    url_for,
    redirect,
    send_from_directory
)


KEYS_DIR = os.path.join("app", "keys")
# KEYS_DIR = os.path.join("keys")


def get_clt_id():
    return open(os.path.join(KEYS_DIR, "clt_id.txt"), "r").read()


def get_clt_secret():
    return open(os.path.join(KEYS_DIR, "clt_secret.txt"), "r").read()


app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(25)
app.config['SESSION_TYPE'] = 'filesystem'
spotify_api = SpotifyAPI(get_clt_id(), get_clt_secret())


@app.before_first_request
def start():
    spotify_api.set_redirect_uri(url_for("save_login", _external=True))


@app.route("/favicon.ico")
def favicon():
    return send_from_directory("Icon", "musik.ico",
                               mimetype="image/vnd.microsoft.icon")


@app.route("/", methods=["GET"])
def homepage():
    if not session.get("token_info", None):
        return redirect(spotify_api.get_oauth().get_authorize_url())
    return redirect(url_for("visualizer"))


@app.route("/save_login", methods=["GET"])
def save_login():
    code = request.args.get("code")
    token_info = spotify_api.get_oauth().get_access_token(code)
    session["token_info"] = token_info
    return redirect(url_for("visualizer"))


@app.route("/visualizer", methods=["GET"])
def visualizer():
    if not session.get("token_info", None):
        return redirect(url_for("homepage"))
    token_manager = TokenManager(session["token_info"], spotify_api)
    return render_template("visualizer.html")


def main():
    app.run(debug=True, host="localhost", port=5000)


if __name__ == '__main__':
    main()
