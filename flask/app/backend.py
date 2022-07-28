import os
import secrets
import json
import shutil
import atexit
import mimetypes
from pathlib import Path

from app.Controller import Controller
from app.Downloader import Downloader
from app.SpotifyAPI import SpotifyAPI
from app.Database import Database

from flask import (
    Flask,
    request,
    session,
    render_template,
    url_for,
    redirect,
    send_from_directory
)
from flask_socketio import SocketIO


CLOSE_WINDOW = "<script>window.onload = window.close();</script>"


class App:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = secrets.token_urlsafe(16)
        self.app.config['SESSION_TYPE'] = "filesystem"

        self.KEYS_DIR = Path(os.path.join("app", "keys"))
        self.DATABASE_DIR = Path(os.path.join("app", "static", "database"))
        self.DEFAULT_CONTROLLER = '{"loop_active": false, "fps": 60, "volume": 0.20}'
        self.REDIRECT_URL = "http://localhost:5000/save_login"
        self.PATH_QUEUE = "queue.json"
        self.PATH_USER_PLAYLISTS = "user_playlists.json"
        self.SPOTIFY_CLT_ID_PATH = os.path.join(
            self.KEYS_DIR, "spotify_clt_id.txt")
        self.SPOTIFY_CLT_SECRET_PATH = os.path.join(
            self.KEYS_DIR, "spotify_clt_secret.txt")

        self.controller = Controller(self)
        self.downloader = Downloader(self)
        self.spotify_api = SpotifyAPI(self)
        self.database = Database(self)
        atexit.register(self.downloader.save_queue)

        self.remove_files()
        self.register_routes()

    @staticmethod
    def run():
        mimetypes.add_type("application/javascript", ".js")
        app = App()
        app.app.env = "development"
        socket_io = SocketIO(app.app)
        socket_io.run(app.app, host="localhost", port=5000, debug=True)

    def remove_files(self):
        # remove _copy and _temp
        for filename in os.listdir(self.DATABASE_DIR):
            if filename.endswith("_copy.mp3") or filename.endswith("_temp.mp3"):
                os.remove(os.path.join(self.DATABASE_DIR, filename))
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
        if os.path.isdir(os.path.join("app", "__pycache__")):
            shutil.rmtree(os.path.join("app", "__pycache__"),
                          ignore_errors=True)

    def register_routes(self):
        @self.app.route("/favicon.ico")
        def favicon():
            return send_from_directory("Icon", "musik.ico",
                                       mimetype="image/vnd.microsoft.icon")

        @self.app.route("/", methods=["GET"])
        def homepage():
            if not session.get("token_info", None):
                return redirect(
                    self.spotify_api.get_oauth().get_authorize_url()
                )
            return redirect(url_for("visualizer"))

        @self.app.route("/save_login", methods=["GET"])
        def save_login():
            code = request.args.get("code")
            session["token_info"] = self.spotify_api.authorize(code)
            return redirect(url_for("visualizer"))

        @self.app.route("/refresh", methods=["GET"])
        def refresh():
            self.spotify_api.save_user_playlists_from_api()
            return CLOSE_WINDOW

        @self.app.route("/play_track", methods=["GET"])
        def play_track():
            if "track_id" in request.args.keys():
                track_id = request.args["track_id"]
                track = self.database.get_track(track_id)
            else:
                track = None
            playlist_id = request.args["playlist_id"]
            playlist = self.database.get_playlist(playlist_id)
            self.controller.play_playlist(playlist, track)
            return redirect(url_for("visualizer", **request.args))

        @self.app.route("/play_random", methods=["GET"])
        def play_random():
            self.controller.play_random_track()
            return redirect(url_for("visualizer"), **request.args)

        @self.app.route("/visualizer", methods=["GET"])
        def visualizer():
            if not session.get("token_info", None):
                return redirect(url_for("homepage"))
            if not self.downloader.running:
                self.downloader.start()
            user_playlists = self.spotify_api.user_playlists_as_list

            controller_web = request.args["controller"] if "controller" in request.args \
                else self.DEFAULT_CONTROLLER
            track = self.controller.get_previous_track() if "back" in request.args \
                else self.controller.get_next_track()

            file_path = os.path.join(
                *self.DATABASE_DIR.parts[1:], track.id_filename)
            return render_template(
                "visualizer.html", file_path=file_path,
                song_name=track.name, controller=controller_web,
                user_playlists=user_playlists, track=json.dumps(
                    track.to_dict(self.spotify_api))
            )
