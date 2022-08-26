import os
import secrets
import shutil
import atexit
from threading import Thread
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
    send_from_directory,
    send_file
)


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
        self.LYRICS_GENIUS_KEY = open(os.path.join(
            self.KEYS_DIR, "lyrics_genius.txt"), "r").read()

        self.controller = Controller(self)
        self.downloader = Downloader(self)
        self.spotify_api = SpotifyAPI(self)
        self.database = Database(self)
        atexit.register(self.downloader.save_queue)

        self.remove_files()
        self.register_routes()

    def remove_files(self):
        if not os.path.isdir(self.DATABASE_DIR):
            os.mkdir(self.DATABASE_DIR)
        # remove _copy and _temp
        for filename in os.listdir(self.DATABASE_DIR):
            if filename.endswith("_copy.mp3") or filename.endswith("_temp.mp3"):
                os.remove(os.path.join(self.DATABASE_DIR, filename))
        for filename in os.listdir("./"):
            # remove not formatted songs
            if filename.endswith(".mp3") \
                    or filename.endswith(".spotdlTrackingFile") \
                or filename.endswith(".zip") \
                    or filename.endswith(".jpg"):
                os.remove(filename)
            # remove tracking files
            if filename.endswith(".spotdlTrackingFile"):
                if os.path.isfile(filename):
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

        @self.app.route("/download_track", methods=["GET"])
        def download_track():
            track_id = request.args.get("track_id")
            track = self.database.get_track(track_id)
            if not os.path.isfile(os.path.join(self.DATABASE_DIR, track.id_filename)):
                self.downloader.download_track(track)
            self.downloader.prepare_downloaded_track(track)
            shutil.copy(os.path.join(self.DATABASE_DIR,
                        track.id_filename), track.filename)
            return send_file(f"../{track.filename}", as_attachment=True)

        @self.app.route("/download_playlist", methods=["GET"])
        def download_playlist():
            playlist_id = request.args.get("playlist_id")
            playlist = self.database.get_playlist(playlist_id)
            for track in playlist.tracks:
                if not os.path.isfile(os.path.join(self.DATABASE_DIR, track.id_filename)):
                    self.downloader.download_track(track)
                self.downloader.prepare_downloaded_track(track)
            directory = playlist.name
            while os.path.isdir(directory):
                directory += "_"
            os.mkdir(directory)
            for track in playlist.tracks:
                shutil.copy(
                    os.path.join(self.DATABASE_DIR, track.id_filename),
                    os.path.join(directory, track.filename)
                )
            shutil.make_archive(directory, "zip", directory)
            shutil.rmtree(directory)
            return send_file(f"../{directory}.zip", as_attachment=True)

        @self.app.route("/refresh", methods=["GET"])
        def refresh():
            def save_user_playlists():
                self.spotify_api.save_user_playlists_from_api()
            Thread(target=save_user_playlists).start()
            return CLOSE_WINDOW

        @self.app.route("/play_track_from_history", methods=["GET"])
        def play_track_from_history():
            track_index = request.args.get("track_index")
            self.controller.play_track_from_history(int(track_index))
            return redirect(url_for("visualizer", **request.args))

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

        @self.app.route("/download_database", methods=["GET"])
        def download_database():
            shutil.make_archive(self.DATABASE_DIR, "zip", self.DATABASE_DIR)
            return send_file(f"../{self.DATABASE_DIR}.zip", as_attachment=True)

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
                "visualizer.html",
                file_path=file_path,
                controller=controller_web,
                user_playlists=user_playlists,
                tracks=self.controller.to_str()
            )
