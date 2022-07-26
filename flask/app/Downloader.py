import os
import shutil
import json
from pathlib import Path
from threading import Thread
from queue import Queue

from app.SpotifyAPI import Track


class Downloader:

    queue: Queue
    queue_items_ids = []
    download_thread: Thread
    running = False

    def __init__(self, app: "App"):
        self.app = app

    def start(self):
        self.queue = self.get_queue()
        self.download_thread = Thread(target=self._worker_save_track,
                                      daemon=True)
        self.download_thread.start()
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

    def get_queue(self) -> Queue:
        queue = Queue()
        if os.path.isfile(self.app.PATH_QUEUE):
            with open(self.app.PATH_QUEUE, 'r') as f:
                tracks = json.load(f)
                for track in tracks:
                    track = Track.from_dict(track)
                    queue.put(track)
                    self.queue_items_ids.append(track.id)
        return queue

    def save_queue(self):
        tracks = []
        try:
            self.queue
        except AttributeError:
            return
        while not self.queue.empty():
            tracks.append(self.queue.get().to_dict(self.app.spotify_api))
            self.queue.task_done()
        with open(self.app.PATH_QUEUE, "w") as f:
            json.dump(tracks, f, indent=4)
        print("TASK DONE")

    def _format_track(self, track: "Track", dir: Path):
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
            self._format_track(track, self.app.DATABASE_DIR)
            # add track data to database
            self.app.database.save_track(track)
            print("Downloaded:", track.filename)
        return track
