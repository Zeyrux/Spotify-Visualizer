import os
import time
import random
import json
from dataclasses import dataclass, field

from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify


PATH_USER_PLAYLISTS = "user_playlists.playlists"


def replace_illegal_chars(path: str) -> str:
    path = path.replace("/", "")
    path = path.replace("\\", "")
    path = path.replace(":", "")
    path = path.replace("*", "")
    path = path.replace("?", "")
    path = path.replace("|", "")
    path = path.replace("\"", "")
    path = path.replace("<", "")
    return path.replace(">", "")


@dataclass
class Artist:
    id: str
    name: str
    spotify_url: str

    def __str__(self):
        return self.name

    @staticmethod
    def from_dict(dictionary: dict) -> "Artist":
        return Artist(
            dictionary["id"],
            dictionary["name"],
            dictionary["spotify_url"]
        )

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name,
                "spotify_url": self.spotify_url}


@dataclass
class Track:
    id: str
    name: str
    spotify_url: str
    artists: list[Artist]
    duration_ms: int
    id_album: str
    album_obj: "Album" = None
    playlists_obj: list["Playlist"] = None
    image_url: str = None
    duration_s: int = field(init=False)
    id_filename: str = field(init=False)
    copy_filename: str = field(init=False)
    temp_filename: str = field(init=False)
    filename: str = field(init=False)

    def __post_init__(self):
        self.duration_s = round(self.duration_ms / 1000)
        self.id_filename = f"{self.id}.mp3"
        self.copy_filename = f"{self.id}_copy.mp3"
        self.temp_filename = f"{self.id}_temp.mp3"
        self.filename = replace_illegal_chars(
            f"{', '.join([str(artist) for artist in self.artists])} - "
            f"{self.name}.mp3"
        )

    def __eq__(self, other: "Track") -> bool:
        return True if other.id == self.id else False

    @staticmethod
    def from_response(response: dict, album_id: str = None):
        artists = []
        for artist in response["artists"]:
            artists.append(Artist(
                artist["id"], artist["name"],
                artist["external_urls"]["spotify"]
            ))

        album_id = response["album"]["id"] if album_id is None else album_id

        return Track(
            response["id"],
            response["name"],
            response["external_urls"]["spotify"],
            artists,
            response["duration_ms"],
            album_id
        )

    @staticmethod
    def from_dict(dictionary: dict) -> "Track":
        return Track(
            dictionary["id"],
            dictionary["name"],
            dictionary["spotify_url"],
            [Artist.from_dict(artist) for artist in dictionary["artists"]],
            dictionary["duration_ms"],
            dictionary["id_album"],
            image_url=dictionary["image_url"]
        )

    def to_dict(self, spotify_api: "SpotifyAPI") -> dict:
        if self.image_url is None:
            self.image_url = spotify_api.get_image_url_of_track(self)
        return {
            "id": self.id, "name": self.name, "spotify_url": self.spotify_url,
            "artists": [artist.to_dict() for artist in self.artists],
            "duration_ms": self.duration_ms, "id_album": self.id_album,
            "image_url": self.image_url
        }

    def album(self, controller: "MusicController") -> "Album":
        if self.album_obj is None:
            self.album_obj = controller.get_album(self.id_album)
        return self.album_obj

    def playlists(self, controller: "MusicController") -> list["Playlist"]:
        if self.playlists_obj is None:
            self.playlists_obj = controller.get_playlists_from_track(self.id)
        return self.playlists_obj


@dataclass
class Album:
    id: str
    name: str
    spotify_url: str
    tracks: list[Track]
    image_url: str
    artists: list[Artist]

    def __str__(self):
        return self.name

    @staticmethod
    def from_response(response: dict) -> "Album":
        album_artists = []
        for album_artist in response["artists"]:
            album_artists.append(Artist(
                album_artist["id"], album_artist["name"],
                album_artist["external_urls"]["spotify"]
            ))

        tracks = []
        for track in response["tracks"]["items"]:
            tracks.append(Track.from_response(track, response["id"]))

        album = Album(response["id"],
                      response["name"],
                      response["external_urls"]["spotify"],
                      tracks,
                      response["images"][0]["url"],
                      album_artists)

        return album

    @staticmethod
    def from_dict(dictionary: dict) -> "Album":
        return Album(
            dictionary["id"],
            dictionary["name"],
            dictionary["spotify_url"],
            [Track.from_dict(track) for track in dictionary["tracks"]],
            dictionary["image_url"]
        )

    def to_dict(self, spotify_api: "SpotifyAPI") -> dict:
        return {
            "id": self.id, "name": self.name, "spotify_url": self.spotify_url,
            "tracks": [track.to_dict(spotify_api) for track in self.tracks],
            "image_url": self.image_url
        }


@dataclass
class Playlist:
    id: str
    name: str
    spotify_url: str
    tracks: list[Track]
    image_url: str

    def __iter__(self):
        for track in self.tracks:
            yield track

    @staticmethod
    def from_response(response: dict) -> "Playlist":
        tracks = []
        for track in response["tracks"]["items"]:
            tracks.append(Track.from_response(track["track"]))
        return Playlist(
            response["id"],
            response["name"],
            response["external_urls"]["spotify"],
            tracks,
            response["images"][0]["url"]
        )

    @staticmethod
    def from_dict(dictionary: dict) -> "Playlist":
        return Playlist(
            dictionary["id"],
            dictionary["name"],
            dictionary["spotify_url"],
            [Track.from_dict(track) for track in dictionary["tracks"]],
            dictionary["image_url"]
        )

    def get_track(self, track_id: str) -> Track:
        for track in self.tracks:
            if track.id == track_id:
                return track

    def to_dict(self, spotify_api: "SpotifyAPI") -> dict:
        return {
            "id": self.id, "name": self.name, "spotify_url": self.spotify_url,
            "tracks": [track.to_dict(spotify_api) for track in self.tracks],
            "image_url": self.image_url
        }


class SpotifyAPI:

    user_playlists: list[Playlist] | None = None
    user_playlists_as_str: str | None = None

    def __init__(self, client_id: str, client_secret: str,
                 redirect_uri: str, controller_pt: "MusicController"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.controller = controller_pt
        self.spotify: Spotify | None = None

    def get_oauth(self) -> SpotifyOAuth:
        return SpotifyOAuth(client_id=self.client_id,
                            client_secret=self.client_secret,
                            scope="user-read-currently-playing",
                            redirect_uri=self.redirect_uri)

    def authorize(self, code: str) -> dict:
        # authorize the user
        token = self.get_oauth().get_access_token(code)
        self.spotify = Spotify(auth=token["access_token"],
                               requests_timeout=1.5, retries=10)
        # initlize user playlists
        if os.path.isfile(PATH_USER_PLAYLISTS):
            self.set_user_playlists()
        else:
            self.save_user_playlists_from_api()
        return token

    def save_user_playlists_from_api(self) -> list[Playlist]:
        # get playlists
        while True:
            try:
                response = self.spotify.current_user_playlists()
                break
            except:
                print("Keine Internet Verbindung")
                time.sleep(2)
        # initilze playlists
        user_playlists = []
        for playlist in response["items"]:
            playlist = self.get_playlist(playlist["id"])
            self.controller.save_playlist(playlist, threaded=True)
            user_playlists.append(playlist)
        self.user_playlists = user_playlists
        user_playlists_as_str = json.dumps([
            playlist.to_dict(self)
            for playlist in self.user_playlists
        ])
        self.user_playlists_as_str = user_playlists_as_str
        self.save_user_playlists()

    def set_user_playlists(self):
        self.user_playlists = []
        with open(PATH_USER_PLAYLISTS, "r") as f:
            self.user_playlists_as_str = f.read()
            for playlist in json.loads(self.user_playlists_as_str):
                playlist = Playlist.from_dict(playlist)
                self.controller.save_playlist(playlist, threaded=True)
                self.user_playlists.append(playlist)

    def save_user_playlists(self):
        with open(PATH_USER_PLAYLISTS, "w") as f:
            f.write(self.user_playlists_as_str)

    def get_playlist(self, id: str) -> Playlist:
        while True:
            try:
                return Playlist.from_response(self.spotify.playlist(id))
            except:
                print("Keine Internet Verbindung")
                time.sleep(2)

    def get_album(self, id: str) -> Album:
        while True:
            try:
                return Album.from_response(self.spotify.album(id))
            except:
                print("Keine Internet Verbindung")
                time.sleep(2)

    def get_track(self, id: str) -> Track:
        while True:
            try:
                return Track.from_response(self.spotify.track(id))
            except:
                print("Keine Internet Verbindung")
                time.sleep(2)

    def _get_recommendation(self, tracks: list[Track],
                            cnt_recommendations: int):
        recommendations = []
        for _ in range(cnt_recommendations):
            if len(tracks) < cnt_recommendations:
                q_tracks = random.choices(tracks,
                                          k=cnt_recommendations)
            else:
                q_tracks = random.sample(tracks,
                                         cnt_recommendations)
                recommendations.append(self.get_recommendation(q_tracks))
        return recommendations

    def get_recommendation(self, tracks: list[Track]) -> Track:
        seed_tracks = [track.id for track in tracks]
        while True:
            try:
                return Track.from_response(
                    self.spotify.recommendations(seed_tracks=seed_tracks,
                                                 limit=1)
                )
            except:
                print("Keine Internet Verbindung")
                time.sleep(2)

    def get_recommendations_for_playlist(
            self, playlist: Playlist, cnt_recommendations: int
    ) -> list[Track]:
        return self._get_recommendation(playlist.tracks, cnt_recommendations)

    def get_recommendations_for_album(
            self, album: Album, cnt_recommendations: int
    ) -> list[Track]:
        return self._get_recommendation(album.tracks, cnt_recommendations)

    def get_album_id_of_track(self, track_id: str) -> str:
        while True:
            try:
                return self.spotify.track(track_id)["album"]["id"]
            except:
                print("Keine Internet Verbindung")
                time.sleep(2)

    def get_image_url_of_track(self, track: Track) -> str:
        img_url = self.controller.get_album_url(track.id_album)
        if img_url is None:
            self.controller.get_album(self.id_album)
            while True:
                try:
                    return self.spotify.track(track.id)["album"]["images"][0]["url"]
                except:
                    print("Keine Internet Verbindung")
                    time.sleep(2)
        return img_url
