import os
import secrets
import json
import shutil
import atexit
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


atexit.register(music_controller.save_queue)


@app.before_first_request
def init():
    # remove _copy and _temp
    for filename in os.listdir(DATABASE_DIR):
        if filename.endswith("_copy.mp3") or filename.endswith("_temp.mp3"):
            os.remove(os.path.join(DATABASE_DIR, filename))
    for filename in os.listdir("./"):
        # remove not formatted songs
        if filename.endswith(".mp3"):
            os.remove(filename)
        # remove tracking files
        if filename.endswith(".spotdlTrackingFile"):
            os.remove(filename)

    # remove .cache and .spotdl-cache
    if os.path.isfile(".cache"):
        os.remove(".cache")
    if os.path.isfile(".spotdl-cache"):
        os.remove(".spotdl-cache")
    # remove spotdl-temp and __pycache__
    if os.path.isdir("spotdl-temp"):
        shutil.rmtree("spotdl-temp", ignore_errors=True)
    if os.path.isdir("__pycache__"):
        shutil.rmtree("__pycache__", ignore_errors=True)
    music_controller.start()


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
    session["token_info"] = music_downloader.spotify_api.authorize(code)
    return redirect(url_for("visualizer"))


@app.route("/refresh", methods=["GET"])
def refresh():
    music_downloader.spotify_api.save_user_playlists_from_api()
    return CLOSE_WINDOW


@app.route("/play_track", methods=["GET"])
def play_track():
    track_id = request.args["track_id"]
    playlist_id = request.args["playlist_id"]
    playlist = music_controller.get_playlist(playlist_id)
    music_controller.tracks.play_playlist(playlist, track_id)
    return redirect(url_for("visualizer", **request.args))


@app.route("/visualizer", methods=["GET"])
def visualizer():
    if not session.get("token_info", None):
        return redirect(url_for("homepage"))
    user_playlists = music_downloader.spotify_api.user_playlists_as_json

    controller = request.args["controller"] if "controller" in request.args \
        else default_controller
    track = music_controller.get_last_song() if "back" in request.args \
        else music_controller.get_song()

    file_path = os.path.join(*DATABASE_DIR.parts[1:], track.id_filename)
    return render_template(
        "visualizer.html", file_path=file_path,
        song_name=track.name, controller=controller,
        user_playlists=user_playlists, track=json.dumps(
            track.to_dict(music_downloader.spotify_api))
    )
