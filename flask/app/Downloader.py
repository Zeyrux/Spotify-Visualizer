import os
import shutil
import json
from urllib.request import urlretrieve
from pathlib import Path
from threading import Thread
from queue import Queue

from app.SpotifyAPI import Track

import eyed3
from eyed3.id3.frames import ImageFrame
import lyricsgenius


class Downloader:

    queue_items_ids = []
    download_thread: Thread
    running = False

    def __init__(self, app: "App"):
        self.app = app
        self.queue = Queue()

    def start(self):
        self.download_thread = Thread(target=self._worker_save_track,
                                      daemon=True)
        self.download_thread.start()
        self.get_queue()
        self.running = True

    def put_queue(self, track: "Track"):
        if track.id in self.queue_items_ids:
            return
        self.queue.put(track)
        self.queue_items_ids.append(track.id)

    def _worker_save_track(self):
        while True:
            track = self.queue.get()
            self.download_track(track)
            self.queue.task_done()
            self.queue_items_ids.remove(track.id)

    def get_queue(self):
        if os.path.isfile(self.app.PATH_QUEUE):
            with open(self.app.PATH_QUEUE, 'r') as f:
                tracks = json.load(f)
                for track in tracks:
                    track = Track.from_dict(track)
                    self.put_queue(track)

    def save_queue(self):
        tracks = []
        try:
            self.queue
        except AttributeError:
            return
        while not self.queue.empty():
            tracks.append(self.queue.get().to_dict(self.app.spotify_api))
            self.queue.task_done()
        if len(tracks) == 0 and len(self.queue_items_ids) == 0:
            return
        with open(self.app.PATH_QUEUE, "w") as f:
            json.dump(tracks, f, indent=4)
        print("TASK DONE")

    def _format_track(self, track: "Track"):
        cpy = os.path.join(self.app.DATABASE_DIR, track.copy_filename)
        temp = os.path.join(self.app.DATABASE_DIR, track.temp_filename)
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
        os.remove(temp)

    def _add_song_data(self, track: "Track"):
        file = eyed3.load(os.path.join(
            self.app.DATABASE_DIR, track.copy_filename))
        if file.tag is None:
            file.initTag()

        try:
            urlretrieve(track.image_url, f"{track.id}.jpg")
            file.tag.images.set(
                ImageFrame.FRONT_COVER,
                open(f"{track.id}.jpg", "rb").read(),
                "image/jpeg"
            )
        except Exception:
            pass

        if file.tag.title is not None:
            file.tag.title = track.name
        if file.tag.artist is not None:
            file.tag.artist = "; ".join(
                [artist.name for artist in track.artists])
        if file.tag.album is not None:
            file.tag.album = track.album(self.app.database).name
        if file.tag.album_artist is not None:
            file.tag.album_artist = "; ".join(
                [artist.name for artist in track.album(
                    self.app.database).artists]
            )

        # get lyrics
        try:
            lg = lyricsgenius.Genius(self.app.LYRICS_GENIUS_KEY)
            if len(track.artists) > 0:
                track_lg = lg.search_song(
                    title=track.name, artist=track.artists[0].name)
            else:
                track_lg = lg.search_song(title=track.name)
            file.tag.lyrics.set(track_lg.lyrics)
        except Exception:
            pass
        file.tag.save()

    def download_track(self, track: "Track") -> "Track":
        if os.path.isfile(os.path.join(self.app.DATABASE_DIR, track.id_filename)):
            if not self.app.database.track_exists(track):
                self.app.database.save_track(track)
            return
        # get track obj
        if type(track).__name__ == "str":
            track = self.app.spotify_api.get_track(track)
        # if track downloaded, exit
        track_path = os.path.join(self.app.DATABASE_DIR, track.copy_filename)
        if os.path.isfile(track_path):
            return
        # move track
        found_track = False
        try:
            os.system(f"spotdl {track.spotify_url}")
        except PermissionError:
            pass
        try:
            shutil.move(track.filename, track_path)
            found_track = True
        except OSError:
            for filename in os.listdir("./"):
                if track.name in filename:
                    shutil.move(filename, track_path)
                    found_track = True
                    break
        if found_track:
            # format track
            self._format_track(track)
            self._add_song_data(track)
            os.rename(
                os.path.join(self.app.DATABASE_DIR, track.copy_filename),
                os.path.join(self.app.DATABASE_DIR, track.id_filename)
            )
            # add track data to database
            self.app.database.save_track(track)
            print("Downloaded:", track.filename)
        return track

    def prepare_downloaded_track(self, track: "Track"):
        copy = os.path.join(self.app.DATABASE_DIR, track.copy_filename)
        final = os.path.join(self.app.DATABASE_DIR, track.id_filename)
        file = eyed3.load(os.path.join(
            self.app.DATABASE_DIR, track.id_filename))
        if file.tag is not None:
            if file.tag.lyrics.get("") is not None:
                return
        shutil.copy(final, copy)
        self._add_song_data(track)
        os.remove(final)
        shutil.move(copy, final)
