import time

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


class Track:
    def __init__(self, spotify_track: dict):
        self.track = spotify_track

    def get_progress_ms(self) -> int:
        return self.track["progress_ms"]

    def get_progress_s(self) -> int:
        return round(self.track["progress_ms"] / 1000)

    def get_duration_ms(self) -> int:
        return self.track["item"]["duration_ms"]

    def get_duration_s(self) -> int:
        return round(self.track["item"]["duration_ms"] / 1000)

    def get_id(self) -> str:
        return self.track["item"]["id"]

    def get_id_filename(self) -> str:
        return self.track["item"]["id"] + ".aac"

    def get_filename(self) -> str:
        return replace_illegal_chars(
            f"{self.get_name()} - {', '.join(self.get_artist_names())}.aac"
        )

    def get_name(self) -> str:
        return self.track["item"]["name"]

    def get_album_name(self) -> str:
        return self.track["item"]["album"]["name"]

    def get_artist_names(self) -> list[str]:
        artists = []
        for artist in self.track["item"]["artists"]:
            artists.append(artist["name"])
        return artists

    def get_album_artist_names(self) -> list[str]:
        artists = []
        for artist in self.track["item"]["album"]["artists"]:
            artists.append(artist["name"])
        return artists


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
                                    token_type: str) -> Track:
        response = requests.get(
            url="https://api.spotify.com/v1/me/player/currently-playing",
            headers={"Authorization": f"{token_type} {access_token}"}
        ).json()
        return Track(response)
