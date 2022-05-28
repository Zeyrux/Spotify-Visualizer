import time
from pathlib import Path

from app.SpotifyAPI import Artist, Album, Track

from mysql import connector
from mysql.connector import connection_cext


class MusicController:
    def __init__(self, path_database: Path):
        self.path_database = path_database
        if not self.path_database.is_dir():
            self.path_database.mkdir(parents=True, exist_ok=True)
        self.last_tracks: list[Track] = []
        self.future_tracks: list[Track] = []

        self.connection: connection_cext.CMySQLConnection | None = None
        self.cursor: connection_cext.CMySQLCursor | None = None

    def is_existing(self, table: str, id: str) -> bool:
        self.cursor.execute(
            f"SELECT * FROM {table} WHERE id = '{id}'"
        )
        for _ in self.cursor:
            self.cursor.reset()
            return True
        return False

    def _get_song_track_from_db(self, song_id) -> Track:
        # song
        self.cursor.execute(f"SELECT name, id_album FROM Song "
                            f"WHERE id = '{song_id}'")
        for song in self.cursor:
            song_name, id_album = song
        self.cursor.reset()

        # song artists
        artists = []
        self.cursor.execute(f"SELECT id_artist FROM SongArtists "
                            f"WHERE id_song = '{song_id}'")
        for artist_id in self.cursor:
            self.cursor.reset()
            self.cursor.execute(f"SELECT * FROM Artist "
                                f"WHERE id = '{artist_id[0]}'")
            for artist in self.cursor:
                self.cursor.reset()
                artists.append(Artist(artist[0], artist[1]))

        # album
        self.cursor.execute(f"SELECT * FROM Album "
                            f"WHERE id = '{id_album}'")
        for album in self.cursor:
            self.cursor.reset()
            album_id, album_name = album

        # album artists
        album_artists = []
        self.cursor.execute(f"SELECT id_artist FROM AlbumArtists "
                            f"WHERE id_album = '{id_album}'")
        for album_artist_id in self.cursor:
            self.cursor.reset()
            self.cursor.execute(f"SELECT * FROM Artist "
                                f"WHERE id = '{album_artist_id}'")
            for album_artist in self.cursor:
                self.cursor.reset()
                album_artists.append(Artist(album_artist[0], album_artist[1]))

        album = Album(album_id, album_name, album_artists)
        return Track(song_id, song_name, artists, album, 0, 0)

    def get_random_song(self) -> Track:
        self.cursor.execute(f"SELECT id FROM Song ORDER BY RAND()")
        for track_id in self.cursor:
            self.cursor.reset()
            return self._get_song_track_from_db(track_id[0])
        self.cursor.reset()

        # if not song exists in database, wait until one is added
        time.sleep(2)
        return self.get_random_song()

    def connect(self):
        config = {
            "user": "root",
            "password": "root",
            "host": "database",
            "port": "3306",
            "database": "Music"
        }
        self.connection = connector.connect(**config)
        self.cursor = self.connection.cursor()

    def save_song(self, track: Track):
        # refresh cur, last track
        self.future_tracks.append(track)

        # insert artists of song
        for artist in track.artists:
            if not self.is_existing("Artist", artist.id):
                sql = f"INSERT INTO Artist (id, name) VALUES " \
                      f"('{artist.id}', '{artist.name}')"
                self.cursor.execute(sql)
                self.cursor.reset()

        # insert album
        if not self.is_existing("Album", track.album.id):
            sql = f"INSERT INTO Album(id, name) VALUES " \
                  f"('{track.album.id}', '{track.album.name}')"
            self.cursor.execute(sql)
            self.cursor.reset()

        # insert song
        if not self.is_existing("Song", track.id):
            sql = f"INSERT INTO Song (id, name, id_album) VALUES " \
                  f"('{track.id}', '{track.name}', '{track.album.id}')"
            self.cursor.execute(sql)
            self.cursor.reset()

        # link song to artists
        if not (self.is_existing("Song", track.id)
                and self.is_existing("Artist", track.artists[0].id)):
            for artist in track.artists:
                sql = f"INSERT INTO SongArtists (id_song, id_artist) VALUES " \
                      f"('{track.id}', '{artist.id}')"
                self.cursor.execute(sql)
                self.cursor.reset()

        # insert artists of album
        for artist in track.album.artists:
            if not self.is_existing("Artist", artist.id):
                sql = f"INSERT INTO Artist (id, name) VALUES " \
                      f"('{artist.id}', '{artist.name}')"
                self.cursor.execute(sql)
                self.cursor.reset()

        # link album to artists
        if not (self.is_existing("Album", track.album.id)
                and self.is_existing("Artist", track.album.artists[0].id)):
            for artist in track.album.artists:
                sql = f"INSERT INTO AlbumArtists (id_album, id_artist) " \
                      f"VALUES ('{track.album.id}', '{artist.id}')"
                self.cursor.execute(sql)
                self.cursor.reset()

        self.connection.commit()

    def get_song(self) -> Track:
        # return future song
        if self.future_tracks:
            future_song = self.future_tracks.pop(0)
            self.last_tracks.append(future_song)
            return future_song

        # return random song
        if not self.last_tracks:
            track = self.get_random_song()
            self.last_tracks.append(track)
            return track

        last_track = self.last_tracks[-1]

        # get song by album
        self.cursor.execute(f"SELECT id FROM Song "
                            f"WHERE id_album = '{last_track}' "
                            f"AND id != '{last_track.id}'")
        for track_id in self.cursor:
            self.cursor.reset()
            track = self._get_song_track_from_db(track_id[0])
            self.last_tracks.append(track)
            return track
        self.cursor.reset()

        # get song by artist
        for artist in last_track.artists:
            self.cursor.execute(f"SELECT id_song FROM SongArtist "
                                f"WHERE id_artist = '{artist.id}' "
                                f"AND id_song != '{last_track.id}'")
            for track_id in self.cursor:
                self.cursor.reset()
                track = self._get_song_track_from_db(track_id[0])
                self.last_tracks.append(track)
                return track
            self.cursor.reset()
