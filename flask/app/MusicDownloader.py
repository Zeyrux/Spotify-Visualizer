import os
import shutil
from pathlib import Path

from app.SpotifyAPI import SpotifyAPI


def get_clt_id(keys_dir: Path):
    return open(os.path.join(keys_dir, "spotify_clt_id.txt"), "r").read()


def get_clt_secret(keys_dir: Path):
    return open(os.path.join(keys_dir, "spotify_clt_secret.txt"), "r").read()


class MusicDownloader:
    def __init__(self, ref_controller: "MusicController",
                 song_dir: Path, keys_dir: Path, redirect_url: str):
        self.controller = ref_controller
        self.song_dir = song_dir

        # api´s
        self.spotify_api = SpotifyAPI(
            get_clt_id(keys_dir), get_clt_secret(keys_dir),
            redirect_url, self.controller
        )

    def _format_song(self, track: "Track", dir: Path):
        cpy = os.path.join(dir, track.copy_filename)
        temp = os.path.join(dir, track.temp_filename)
        final = os.path.join(dir, track.id_filename)
        # change codec
        os.system(
            f"ffmpeg -y -loglevel quiet -i "
            f"\"{cpy}\" -acodec mp3 -vcodec copy \"{temp}\""
        )
        # remove silent in begin and end
        os.system(
            f"ffmpeg -y -loglevel quiet -i "
            f"\"{temp}\" "
            f"-af silenceremove=start_periods=1:start_silence=0.1:"
            f"start_threshold=-50dB,areverse,"
            f"silenceremove=start_periods=1:start_silence=0.1:"
            f"start_threshold=-50dB,areverse "
            f"\"{cpy}\""
        )
        # normalize volume
        os.system(
            f"ffmpeg -y -loglevel quiet -i "
            f"\"{cpy}\" -af 'volume=1dB' \"{cpy}\""
        )
        os.rename(cpy, final)
        os.remove(temp)

    def download_song(self, track: "Track") -> "Track":
        if os.path.isfile(os.path.join(self.song_dir, track.id_filename)):
            return
        # get track obj
        if type(track).__name__ == "str":
            track = self.spotify_api.get_track(track)
        # if song downloaded, exit
        song_path = os.path.join(self.song_dir, track.copy_filename)
        if os.path.isfile(song_path):
            return
        # move song
        found_track = False
        try:
            os.system(f"spotdl {track.spotify_url}")
        except PermissionError:
            pass
        try:
            shutil.move(track.filename, song_path)
            found_track = True
        except OSError:
            for filename in os.listdir("./"):
                if track.name in filename:
                    shutil.move(filename, song_path)
                    found_track = True
                    break
        if found_track:
            # format song
            self._format_song(track, self.song_dir)
            # add song data to database
            self.controller.save_song(track)
            print("Downloaded:", track.filename)
        return track
