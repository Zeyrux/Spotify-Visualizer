import time
import os
from threading import Thread
from pathlib import Path

from app.SpotifyAPI import SpotifyAPI
from app.YoutubeAPI import YoutubeAPI
from app.YoutubeAppsBuilder import YoutubeAppsBuilder


import eyed3
from eyed3.id3.frames import ImageFrame
from urllib.request import urlretrieve


def get_clt_id(keys_dir: Path):
    return open(os.path.join(keys_dir, "spotify_clt_id.txt"), "r").read()


def get_clt_secret(keys_dir: Path):
    return open(os.path.join(keys_dir, "spotify_clt_secret.txt"), "r").read()


class MusicDownloader:

    token_info: dict | None = None

    def __init__(self, ref_controller: "MusicController",
                 song_dir: Path, keys_dir: Path, redirect_url: str):
        self.controller = ref_controller
        self.song_dir = song_dir

        # api´s
        self.spotify_api = SpotifyAPI(
            get_clt_id(keys_dir), get_clt_secret(keys_dir), redirect_url
        )
        self.youtube_api = YoutubeAPI(
            YoutubeAppsBuilder(os.path.join(keys_dir, "youtube.txt"))
        )

    def _format_song(self, path_song: str):
        cpy_path = path_song[:path_song.rindex('.')] \
                   + "copy" + path_song[path_song.rindex('.'):]
        # change codec
        os.system(
            f"ffmpeg -y -loglevel quiet -i "
            f"\"{path_song}\" -acodec mp3 -vcodec copy \"{cpy_path}\""
        )
        # remove silent begin and end
        os.system(
            f"ffmpeg -y -loglevel quiet -i "
            f"\"{cpy_path}\" "
            f"-af silenceremove=start_periods=1:start_silence=0.1:"
            f"start_threshold=-50dB,areverse,"
            f"silenceremove=start_periods=1:start_silence=0.1:"
            f"start_threshold=-50dB,areverse "
            f"\"{path_song}\""
        )
        # normalize volume
        os.system(
            f"ffmpeg -y -loglevel quiet -i "
            f"{path_song} -af 'volume=1dB' {path_song}"
        )
        os.remove(cpy_path)

    def _add_thumbnail(self, path_song: str, track: "Track"):
        thumbnail_path = path_song[:path_song.rindex(".")] + "thumbnail.jpeg"
        # get thumbnail
        urlretrieve(track.album(self.controller).image_url, thumbnail_path)

        # add thumbnail
        file = eyed3.load(path_song)
        if file.tag is None:
            file.initTag()
        file.tag.images.set(ImageFrame.FRONT_COVER,
                            open(thumbnail_path, "rb").read(),
                            "image/jpeg")
        file.tag.save()
        os.remove(thumbnail_path)

    def _add_song_data(self, path_song: str, track: "Track"):
        file = eyed3.load(path_song)
        if file.tag is None:
            file.initTag()

        file.tag.artist = "; ".join([str(artist) for artist in track.artists])
        file.tag.album = track.album(self.controller).name
        file.tag.album_artist = "; ".join(
            [str(artist) for artist in track.album(self.controller).artists]
        )
        file.tag.title = track.name
        file.tag.save()

    def download_cur_song(self):
        track = self.spotify_api.get_currently_playing_track()
        # if no song found, exit
        if track is None:
            return
        # if song downloaded, exit
        if self.controller.is_existing("Song", track.id):
            return
        # search for track
        pytube_obj = self.youtube_api.search_song(track)
        # download track
        self.youtube_api.download(pytube_obj, self.song_dir, track.id_filename)
        path_song = os.path.join(self.song_dir, track.id_filename)
        # format song, add thumbnail, add song data
        self._format_song(path_song)
        self._add_thumbnail(path_song, track)
        self._add_song_data(path_song, track)
        # add song data to database
        self.controller.save_song(track, True)
        print("Downloaded:", track.filename)

    def start(self, token_info: dict):
        self.token_info = token_info

        Thread(target=self.run, daemon=True).start()

    def run(self):
        while True:
            self.download_cur_song()
            time.sleep(10)
