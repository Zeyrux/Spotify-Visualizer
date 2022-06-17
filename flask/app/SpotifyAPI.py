import base64
import datetime
from json.decoder import JSONDecodeError
import time
from dataclasses import dataclass, field
from urllib.parse import urlencode

import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify


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

    def __str__(self):
        return self.name


@dataclass
class Track:
    id: str
    name: str
    artists: list[Artist]
    duration_ms: int
    date_played: datetime.date = datetime.date.today()
    cnt_played: int = 0
    duration_s: int = field(init=False)
    id_filename: str = field(init=False)
    filename: str = field(init=False)

    def __post_init__(self):
        self.duration_s = round(self.duration_ms / 1000)
        self.id_filename = f"{self.id}.mp3"
        self.filename = replace_illegal_chars(
            f"{self.name} - "
            f"{', '.join([str(artist) for artist in self.artists])}.mp3"
        )

    def __eq__(self, other: "Track") -> bool:
        return True if other.id == self.id else False

    @staticmethod
    def from_response(response: dict):
        artists = []
        for artist in response["artists"]:
            artists.append(Artist(artist["id"], artist["name"]))
        kwargs = {"progress_ms": response["progress_ms"]} \
            if "progress_ms" in response.values() else {}

        return Track(
            response["id"],
            response["name"],
            artists,
            response["duration_ms"],
            **kwargs
        )


@dataclass
class Album:
    id: str
    name: str
    tracks: list[Track]
    image_url: str
    artists: list[Artist]

    def __str__(self):
        return self.name

    @staticmethod
    def from_response(response: dict) -> "Album":
        album_artists = []
        for album_artist in response["artists"]:
            album_artists.append(Artist(album_artist["id"],
                                        album_artist["name"]))

        tracks = []
        for track in response["tracks"]["items"]:
            tracks.append(Track.from_response(track))

        album = Album(response["id"],
                      response["name"],
                      tracks,
                      response["images"][0]["url"],
                      album_artists)
        return album


@dataclass
class Playlist:
    id: str
    name: str
    tracks: list[Track]

    def __iter__(self):
        for track in self.tracks:
            yield track

    @staticmethod
    def from_request(response: dict) -> "Playlist":
        id = response["id"]
        name = response["name"]
        tracks = []
        for track in response["tracks"]["items"]:
            tracks.append(Track.from_response(track["track"]))
        return Playlist(id, name, tracks)


class SpotifyAPI:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.spotify: Spotify | None = None

    def get_oauth(self) -> SpotifyOAuth:
        return SpotifyOAuth(client_id=self.client_id,
                            client_secret=self.client_secret,
                            scope="user-read-currently-playing",
                            redirect_uri=self.redirect_uri)

    def authorize(self, code: str) -> dict:
        token = self.get_oauth().get_access_token(code)
        self.spotify = Spotify(auth=token["access_token"])
        return token

    def get_playlist(self, id: str) -> Playlist:
        return Playlist.from_request(self.spotify.playlist(id))

    def get_album(self, id: str) -> Album:
        return Album.from_response(self.spotify.album(id))

    def get_track(self, id: str) -> Track:
        return Track.from_response(self.spotify.track(id))
