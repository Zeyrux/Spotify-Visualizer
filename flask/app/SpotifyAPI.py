import time
import random
from dataclasses import dataclass, field

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
    id_album: str
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

        return Track(
            response["id"],
            response["name"],
            artists,
            response["duration_ms"],
            response["album"]["id"]
        )

    def album(self, controller: "MusicController") -> "Album":
        return controller.get_album(self.id_album)

    def playlists(self, controller: "MusicController") -> list["Playlist"]:
        return controller.get_playlist_with_track(self.id)


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
        return Track.from_response(
            self.spotify.recommendations(seed_tracks=seed_tracks, limit=1)
        )

    def get_recommendations_for_playlist(
            self, playlist: Playlist, cnt_recommendations: int
    ) -> list[Track]:
        return self._get_recommendation(playlist.tracks, cnt_recommendations)

    def get_recommendations_for_album(
            self, album: Album, cnt_recommendations: int
    ) -> list[Track]:
        return self._get_recommendation(album.tracks, cnt_recommendations)

    def get_currently_playing_track(self) -> Track:
        track = None
        while track is None:
            track = self.spotify.currently_playing()
            time.sleep(2)
        return Track.from_response(track["item"])
