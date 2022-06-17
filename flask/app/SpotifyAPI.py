import base64
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
    progress_ms: int = 0
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
        item_access = "item" if "item" in response.values() else "track"
        artists = []
        for artist in response[item_access]["artists"]:
            artists.append(Artist(artist["id"], artist["name"]))

        album_artists = []
        for album_artist in response[item_access]["album"]["artists"]:
            album_artists.append(Artist(album_artist["id"],
                                        album_artist["name"]))

        album = Album(response[item_access]["album"]["id"],
                      response[item_access]["album"]["name"],
                      response[item_access]["album"]["images"][0]["url"],
                      album_artists)

        kwargs = {"progress_ms": response["progress_ms"]} \
            if "progress_ms" in response.values() else {}

        return Track(
            response[item_access]["id"],
            response[item_access]["name"],
            artists,
            album,
            response[item_access]["duration_ms"],
            **kwargs
        )


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
            tracks.append(Track.from_response(track))
        print(tracks)
        return Playlist(id, name, tracks)


class AccessToken:
    def __init__(self, access_token: str, token_type: str, expires_in: float):
        self.token = access_token
        self.token_type = token_type
        self.expires = datetime.datetime.now() \
                       + datetime.timedelta(seconds=expires_in)

    @staticmethod
    def from_json(data) -> "AccessToken":
        return AccessToken(data["access_token"],
                           data["token_type"],
                           data["expires_in"])

    def is_expired(self) -> bool:
        return datetime.datetime.now() > self.expires


class TokenManagerClient:
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


class TokenManagerSpotify:
    def __init__(self, access_token: AccessToken, spotify_api: "SpotifyAPI"):
        self.access_token = access_token
        self.spotify_api = spotify_api

    def get_access_token(self) -> AccessToken:
        if self.access_token.is_expired():
            self.access_token = self.spotify_api.authorize()
        return self.access_token


class SpotifyAPI:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = None

        self.url_token_spotify = "https://accounts.spotify.com/api/token"
        self.token_data_spotify = {"grant_type": "client_credentials"}
        client_creds = (base64.b64encode(
            f'{client_id}:{client_secret}'.encode())
        ).decode()
        self.header_authorize_spotify = {
            "Authorization": f"basic {client_creds}"
        }

    def authorize(self) -> AccessToken:
        response = requests.post(self.url_token_spotify,
                                 data=self.token_data_spotify,
                                 headers=self.header_authorize_spotify)
        if response.status_code not in range(200, 299):
            raise Exception(
                f"could not authorizse; STATUS: {response.status_code}")
        return AccessToken.from_json(response.json())

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

    def get_playlist(self, id: str, access_token: AccessToken) -> Playlist:
        a = requests.get(
            f"https://api.spotify.com/v1/playlists/{id}",
            headers={"Authorization": f"{access_token.token_type} "
                                      f"{access_token.token}"}
        )
        b = a.json()
        c = Playlist.from_request(b)
        return c
