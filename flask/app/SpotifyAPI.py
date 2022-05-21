import time

import requests
from spotipy.oauth2 import SpotifyOAuth


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

    def get_currently_playing_track(self, access_token: str, token_type: str):
        response = requests.get(
            url="https://api.spotify.com/v1/me/player/currently-playing",
            headers={"Authorization": f"{token_type} {access_token}"}
        )
        return response.json()
t = "test"