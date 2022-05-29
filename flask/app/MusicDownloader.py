import time
import os
from threading import Thread
from pathlib import Path

from app.SpotifyAPI import SpotifyAPI, TokenManager
from app.YoutubeAPI import YoutubeAPI
from app.YoutubeAppsBuilder import YoutubeAppsBuilder


def get_clt_id(keys_dir: Path):
    return open(os.path.join(keys_dir, "spotify_clt_id.txt"), "r").read()


def get_clt_secret(keys_dir: Path):
    return open(os.path.join(keys_dir, "spotify_clt_secret.txt"), "r").read()


class MusicDownloader:

    token_info: dict | None = None

    def __init__(self, ref_controller: "MusicController",
                 song_dir: Path, keys_dir: Path):
        self.controller = ref_controller
        self.song_dir = song_dir

        # api´s
        self.spotify_api = SpotifyAPI(get_clt_id(keys_dir),
                                      get_clt_secret(keys_dir))
        self.youtube_api = YoutubeAPI(
            YoutubeAppsBuilder(os.path.join(keys_dir, "youtube.txt"))
        )

    def download_cur_song(self):
        token_manager = TokenManager(self.token_info, self.spotify_api)
        # get cur track
        track = self.spotify_api.get_currently_playing_track(
            token_manager.get_access_token(), token_manager.get_token_type()
        )
        # if not song found exit
        if track is None:
            return
        # if song downloaded exit
        if self.controller.is_existing("Song", track.id):
            return
        # search for track
        pytube_obj = self.youtube_api.search_song(track)
        # download track
        self.youtube_api.download(pytube_obj, self.song_dir, track.id_filename)
        # add song data to database
        self.controller.save_song(track)
        print("Downloaded:", track.filename)

    def start(self, token_info: dict):
        self.token_info = token_info

        Thread(target=self.run, daemon=True).start()

    def run(self):
        while True:
            self.download_cur_song()
            time.sleep(10)
