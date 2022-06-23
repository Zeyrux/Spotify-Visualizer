import os
import secrets
from pathlib import Path

from app.MusicDownloader import MusicDownloader
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


KEYS_DIR = Path(os.path.join("app", "keys"))
DATABASE_DIR = Path(os.path.join("app", "static", "database"))


def get_clt_id():
    return open(os.path.join(KEYS_DIR, "spotify_clt_id.txt"), "r").read()


def get_clt_secret():
    return open(os.path.join(KEYS_DIR, "spotify_clt_secret.txt"), "r").read()


CLOSE_WINDOW = "<script>window.onload = window.close();</script>"

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(25)
app.config['SESSION_TYPE'] = 'filesystem'

music_controller = MusicController(DATABASE_DIR)
music_downloader = MusicDownloader(
    music_controller, DATABASE_DIR,
    KEYS_DIR, "http://localhost:5000/save_login"
)
music_controller.downloader = music_downloader

default_controller = '{"loop_active": false, "fps": 60, "volume": 0.20}'


@app.before_first_request
def start():
    music_controller.connect()


@app.route("/favicon.ico")
def favicon():
    return send_from_directory("Icon", "musik.ico",
                               mimetype="image/vnd.microsoft.icon")


@app.route("/", methods=["GET"])
def homepage():
    if not session.get("token_info", None):
        return redirect(
            music_downloader.spotify_api.get_oauth().get_authorize_url()
        )
    return redirect(url_for("visualizer"))


@app.route("/save_login", methods=["GET"])
def save_login():
    code = request.args.get("code")
    token_info = music_downloader.spotify_api.authorize(code)
    session["token_info"] = token_info
    music_downloader.start(token_info)
    return redirect(url_for("visualizer"))


@app.route("/add_playlist", methods=["POST"])
def add_playlist():
    return "Hallo"


@app.route("/play_track", methods=["GET"])
def play_track():
    track_id = request.args["track"]
    track = music_downloader.download_song(track_id)
    music_controller.tracks.add_next_track(track)
    return redirect(url_for("visualizer", **request.args))


@app.route("/visualizer", methods=["GET"])
def visualizer():
    if not session.get("token_info", None):
        return redirect(url_for("homepage"))

    controller = request.args["controller"] if "controller" in request.args \
        else default_controller
    track = music_controller.get_last_song() if "back" in request.args \
        else music_controller.get_song()

    file_path = os.path.join(*DATABASE_DIR.parts[1:], track.id_filename)
    user_playlists = music_downloader.spotify_api.get_user_playlists(True)
    return render_template(
        "visualizer.html", file_path=file_path,
        song_name=track.name, controller=controller,
        user_playlists=user_playlists
    )
