import datetime
from json.decoder import JSONDecodeError
import time
from dataclasses import dataclass, field

import requests
from spotipy.oauth2 import SpotifyOAuth


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
class Album:
    id: str
    name: str
    image_url: str
    artists: list[Artist]

    def __str__(self):
        return self.name


@dataclass
class Track:
    id: str
    name: str
    artists: list[Artist]
    album: Album
    duration_ms: int
    progress_ms: int
    date_played: datetime.date = datetime.date.today()
    cnt_played: int = 0
    duration_s: int = field(init=False)
    progress_s: int = field(init=False)
    id_filename: str = field(init=False)
    filename: str = field(init=False)

    def __post_init__(self):
        self.duration_s = round(self.duration_ms / 1000)
        self.progress_s = round(self.progress_ms / 1000)
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
        for artist in response["item"]["artists"]:
            artists.append(Artist(artist["id"], artist["name"]))

        album_artists = []
        for album_artist in response["item"]["album"]["artists"]:
            album_artists.append(Artist(album_artist["id"],
                                        album_artist["name"]))

        album = Album(response["item"]["album"]["id"],
                      response["item"]["album"]["name"],
                      response["item"]["album"]["images"][0]["url"],
                      album_artists)

        return Track(
            response["item"]["id"],
            response["item"]["name"],
            artists,
            album,
            response["item"]["duration_ms"],
            response["progress_ms"]
        )


class TokenManager:
    def __init__(self, token_info: dict, spotify_api: "SpotifyAPI"):
        self.token_info = token_info
        self.spotify_api = spotify_api

    def _set_new_token(self):
        oauth = self.spotify_api.get_oauth()
        self.token_info = oauth.refresh_access_token(
            self.token_info["refresh_token"]
        )

    def get_token(self) -> dict:
        now = int(time.time())
        if self.token_info["expires_at"] - now < 60:
            self._set_new_token()
        return self.token_info

    def get_access_token(self) -> str:
        return self.get_token()["access_token"]

    def get_token_type(self) -> str:
        return self.get_token()["token_type"]


class SpotifyAPI:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = None

    def set_redirect_uri(self, redirect_uri: str):
        if self.redirect_uri is None:
            self.redirect_uri = redirect_uri

    def get_oauth(self) -> SpotifyOAuth:
        return SpotifyOAuth(client_id=self.client_id,
                            client_secret=self.client_secret,
                            scope="user-read-currently-playing",
                            redirect_uri=self.redirect_uri)

    def get_currently_playing_track(self, access_token: str,
                                    token_type: str) -> Track | None:
        try:
            response = requests.get(
                url="https://api.spotify.com/v1/me/player/currently-playing",
                headers={"Authorization": f"{token_type} {access_token}"}
            ).json()
        except JSONDecodeError:
            return
        if response["item"] is None:
            return
        return Track.from_response(response)
