import os
import secrets

from app.SpotifyAPI import SpotifyAPI, TokenManager
from app.YoutubeAPI import YoutubeAPI
from app.YoutubeAppsBuilder import YoutubeAppsBuilder
from app.MusicController import MusicController

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
DATABASE_DIR = os.path.join("app", "static", "database")


def get_clt_id():
    return open(os.path.join(KEYS_DIR, "spotify_clt_id.txt"), "r").read()


def get_clt_secret():
    return open(os.path.join(KEYS_DIR, "spotify_clt_secret.txt"), "r").read()


CLOSE_WINDOW = "<script>window.onload = window.close();</script>"

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(25)
app.config['SESSION_TYPE'] = 'filesystem'

spotify_api = SpotifyAPI(get_clt_id(), get_clt_secret())
youtube_api = YoutubeAPI(
    YoutubeAppsBuilder(os.path.join(KEYS_DIR, "youtube.txt"))
)
music_controller = MusicController(DATABASE_DIR)


def download_cur_song(token_info) -> tuple["Track", "TokenManager"]:
    token_manager = TokenManager(token_info, spotify_api)
    # get cur track
    track = spotify_api.get_currently_playing_track(
        token_manager.get_access_token(), token_manager.get_token_type()
    )
    # search for track
    pytube_obj = youtube_api.search_song(track)
    # download track
    youtube_api.download(pytube_obj, DATABASE_DIR, track.id_filename)
    return track, token_manager


@app.before_first_request
def start():
    # music_controller.connect()
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


@app.route("/skip", methods=["GET"])
def skip():
    pass


@app.route("/visualizer", methods=["GET"])
def visualizer():
    if not session.get("token_info", None):
        return redirect(url_for("homepage"))
    track, token_manager = download_cur_song(
        session["token_info"]
    )
    file_path = os.path.join(DATABASE_DIR.replace("app", ""),
                             track.id_filename)
    return render_template(
        "visualizer.html", file_path=file_path, song_name=track.name
    )
