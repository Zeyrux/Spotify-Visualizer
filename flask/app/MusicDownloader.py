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

    def download_song(self, track: "Track") -> "Track":
        # get track obj
        if type(track).__name__ == "str":
            track = self.spotify_api.get_track(track)
        # if song downloaded, exit
        if self.controller.is_existing("Song", track.id):
            return
        os.system(f"spotdl {track.spotify_url}")
        shutil.rmtree("spotdl-temp", ignore_errors=True)
        for path in os.listdir("./"):
            if ".mp3" in path:
                song_path = os.path.join(self.song_dir, track.id_filename)
                shutil.move(path, song_path)
                self._format_song(song_path)
        # add song data to database
        self.controller.save_song(track, add_future_tracks=True)
        print("Downloaded:", track.filename)
        return track
