import random
import time
import os
import json
from itertools import count

from app.SpotifyAPI import Playlist, Album, Track


class Tracks:

    last_call_next: bool = None

    def __init__(self, tracks=None):
        self.tracks = [] if tracks is None else tracks
        self.cur_track = -1

    def next(self) -> Track:
        self.last_call_next = True
        self.cur_track += 1
        return self.tracks[self.cur_track]

    def previous(self) -> Track:
        self.last_call_next = False
        self.cur_track -= 1
        return self.tracks[self.cur_track]

    def current(self) -> Track:
        return self.tracks[self.cur_track]

    def next_exists(self) -> bool:
        return self.cur_track + 1 < len(self.tracks)

    def previous_exists(self) -> bool:
        return self.cur_track - 1 >= 0

    def add_previous(self, track: Track):
        self.tracks.insert(self.cur_track, track)
        self.cur_track += 1

    def set_next(self, track: Track):
        self.tracks.insert(self.cur_track + 1, track)

    def add_future(self, track: Track):
        self.tracks.append(track)

    def del_current(self):
        del self.tracks[self.cur_track]
        if self.last_call_next:
            self.cur_track -= 1

    def __iter__(self):
        for track in self.tracks:
            yield track


class RandomPlayer:

    force_play_next = False

    def __init__(self, app: "App") -> None:
        self.app = app
        self.tracks = Tracks()

    def get_next_track(self):
        if not self.tracks.next_exists():
            self.tracks.add_future(self.app.database.get_random_track())
            self.force_play_next = False
        else:
            self.force_play_next = True
        return self.tracks.next()

    def get_previous_track(self):
        if not self.tracks.previous_exists():
            self.tracks.add_previous(self.app.database.get_random_track())
            self.force_play_next = False
        else:
            self.force_play_next = True
        return self.tracks.previous()


class SpecificPlayer:

    force_play_next = False

    def __init__(self, app: "App", tracks: list[Track]) -> None:
        self.app = app
        self.tracks = Tracks()
        self.tracks_to_play = tracks

    def get_next_track(self):
        if not self.tracks.next_exists():
            self.tracks.add_future(random.choice(self.tracks_to_play))
            self.force_play_next = False
        else:
            self.force_play_next = True
        return self.tracks.next()

    def get_previous_track(self):
        if not self.tracks.previous_exists():
            self.tracks.add_previous(random.choice(self.tracks_to_play))
            self.force_play_next = False
        else:
            self.force_play_next = True
        return self.tracks.previous()


class Controller:
    def __init__(self, app: "App") -> None:
        self.app = app
        self.player = RandomPlayer(self.app)

    def check_track(self, function) -> Track:
        track = function()
        if self.player.force_play_next:
            if not os.path.isfile(os.path.join(self.app.DATABASE_DIR, track.id_filename)):
                self.app.downloader.download_track(track)
            return track
        for counter_new_tries in count():
            if counter_new_tries == 50:
                self.app.downloader.download_track(track)
            if os.path.isfile(os.path.join(self.app.DATABASE_DIR, track.id_filename)):
                return track
            self.player.tracks.del_current()
            self.app.downloader.put_queue(track)
            time.sleep(0.05)
            track = function()

    def get_next_track(self):
        return self.check_track(self.player.get_next_track)

    def get_previous_track(self):
        return self.check_track(self.player.get_previous_track)

    def play_playlist(self, playlist: Playlist, next_track: Track = None):
        self.player = SpecificPlayer(self.app, playlist.tracks)
        if next_track is not None:
            self.player.tracks.set_next(next_track)

    def play_album(self, album: Album, next_track: Track = None):
        self.player = SpecificPlayer(self.app, album.tracks)
        if next_track is not None:
            self.player.tracks.set_next(next_track)

    def play_random_track(self):
        self.player = RandomPlayer(self.app)

    def play_track_from_history(self, track_index):
        self.player.tracks.cur_track = track_index - 1

    def to_str(self) -> str:
        tracks = []
        for track in self.player.tracks:
            tracks.append(track.to_dict(self.app.spotify_api))
            print(track.to_dict(self.app.spotify_api))

        return json.dumps({
            "tracks": tracks,
            "cur_track": self.player.tracks.cur_track,
        })
