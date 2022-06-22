import time
from pathlib import Path

from app.SpotifyAPI import Artist, Album, Playlist, Track

from mysql import connector
from mysql.connector import connection_cext


class Tracks:
    def __init__(self):
        self.tracks = []
        self.cur_track = -1

    def __str__(self):
        return f"Tracks(pt: {self.cur_track}, tracks: " \
               f"[{','.join([track.name for track in self.tracks])}])"

    def add_future_track(self, track: Track):
        self.tracks.append(track)

    def future_song_exists(self) -> bool:
        return len(self.tracks) > self.cur_track + 1

    def get_future_song(self) -> Track:
        self.cur_track += 1
        return self.tracks[self.cur_track]

    def add_last_track(self, track: Track):
        self.tracks.insert(self.cur_track, track)
        self.cur_track += 1

    def get_last_song(self) -> Track:
        self.cur_track -= 1
        return self.tracks[self.cur_track]

    def last_song_exists(self) -> bool:
        return self.cur_track > 0

    def last_song(self) -> Track:
        return self.tracks[self.cur_track - 1]

    def get_cur_song(self) -> Track:
        return self.tracks[self.cur_track]

    def cur_song_exists(self) -> bool:
        return len(self.tracks) > 0

    def skip_song(self):
        self.cur_track += 1


class MusicController:
    def __init__(self, path_database: Path):
        self.path_database = path_database
        if not self.path_database.is_dir():
            self.path_database.mkdir(parents=True, exist_ok=True)
        self.tracks = Tracks()

        self.connection: connection_cext.CMySQLConnection | None = None
        self.cursor: connection_cext.CMySQLCursor | None = None
        self.spotify_api: "SpotifyAPI" | None = None

    def connect(self):
        config = {
            "user": "root",
            "password": "root",
            # "host": "database",
            "host": "localhost",
            "port": "3306",
            "database": "Music"
        }
        self.connection = connector.connect(**config)
        self.cursor = self.connection.cursor()

    def _get_song_from_db(self, song_id) -> Track:
        # song
        sql = f"SELECT name, id_album, duration_ms " \
              f"FROM Song WHERE id = '{song_id}'"
        self.cursor.execute(sql)
        song_name, album_id, duration_ms = self.cursor.fetchone()
        self.cursor.reset()

        # song artists
        artists = []
        self.cursor.execute(f"SELECT id_artist FROM SongArtists "
                            f"WHERE id_song = '{song_id}'")
        for artist_id in self.cursor:
            self.cursor.reset()
            self.cursor.execute(f"SELECT name FROM Artist "
                                f"WHERE id = '{artist_id[0]}'")
            artist_name = self.cursor.fetchone()[0]
            artists.append(Artist(artist_id[0], artist_name))
            self.cursor.reset()

        return Track(
            song_id, song_name, artists, duration_ms, album_id
        )

    def is_existing(self, table: str, id: str) -> bool:
        self.cursor.execute(f"SELECT * FROM {table} WHERE id = '{id}'")
        exists = False if self.cursor.fetchone() is None else True
        self.cursor.reset()
        return exists

    def get_playlist(self, playlist_id: str) -> Playlist:
        if not self.is_existing("Playlist", playlist_id):
            playlist = self.spotify_api.get_playlist(playlist_id)
            self.save_playlist(playlist)

        self.cursor.execute(f"SELECT name FROM Playlist "
                            f"WHERE id = '{playlist_id}'")
        playlist_name, = self.cursor.fetchone()
        self.cursor.reset()

        # songs
        songs = []
        self.cursor.execute(f"SELECT id_song FROM Playlist "
                            f"WHERE id_playlist = '{playlist_id}'")
        for song_id in self.cursor:
            songs.append(self._get_song_from_db(song_id))
        self.cursor.reset()

        return Playlist(playlist_id, playlist_name, songs)

    def get_album(self, album_id: str) -> Album:
        if not self.is_existing("Album", album_id):
            album = self.spotify_api.get_album(album_id)
            self.save_album(album)

        self.cursor.execute(f"SELECT name, image_url FROM Album "
                            f"WHERE id = '{album_id}'")
        album_name, album_img_url = self.cursor.fetchone()
        self.cursor.reset()

        # album artists
        album_artists = []
        self.cursor.execute(f"SELECT id_artist FROM AlbumArtists "
                            f"WHERE id_album = '{album_id}'")
        for album_artist_id in self.cursor:
            self.cursor.reset()
            sql = f"SELECT * FROM Artist WHERE id = '{album_artist_id[0]}'"
            self.cursor.execute(sql)
            album_artist = self.cursor.fetchone()
            album_artists.append(Artist(album_artist[0], album_artist[1]))
            self.cursor.reset()

        # songs
        songs = []
        self.cursor.execute(f"SELECT id FROM Song "
                            f"WHERE id_album = '{album_id}'")
        for song_id in self.cursor:
            songs.append(self._get_song_from_db(song_id[0]))
        self.cursor.reset()

        return Album(
            album_id, album_name, songs, album_img_url, album_artists
        )

    def get_playlists_from_track(self, track_id: str) -> list[Playlist]:
        if not self.is_existing("Song", track_id):
            track = self.spotify_api.get_track(track_id)
            self.save_song(track)

        sql = f"SELECT id_playlist FROM SongPlaylist " \
              f"WHERE id_song = '{track_id}'"
        self.cursor.execute(sql)
        playlists = []
        for playlist_id in self.cursor:
            playlists.append(self.get_playlist(playlist_id))
        self.cursor.reset()
        return playlists

    def get_random_song(self) -> Track:
        self.cursor.execute(f"SELECT id FROM Song ORDER BY RAND()")
        for track_id in self.cursor:
            self.cursor.reset()
            return self._get_song_from_db(track_id[0])
        self.cursor.reset()

        # if not song exists in database, wait until one is added
        time.sleep(2)
        return self.get_random_song()

    def save_song(self, track: Track, add_future_tracks=False):
        # refresh cur, last track
        if add_future_tracks:
            self.tracks.add_future_track(track)

        # insert artists of song
        for artist in track.artists:
            artist_name = artist.name.replace("'", "\\'")
            sql = f"INSERT IGNORE INTO Artist (id, name) VALUES " \
                  f"('{artist.id}', '{artist_name}')"
            self.cursor.execute(sql)
            self.cursor.reset()

        # insert song
        track_name = track.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Song " \
              f"(id, name, id_album, duration_ms) VALUES " \
              f"('{track.id}', '{track_name}', " \
              f"'{track.id_album}', '{track.duration_ms}')"
        self.cursor.execute(sql)
        self.cursor.reset()

        # link song to artists
        for artist in track.artists:
            sql = f"INSERT IGNORE INTO SongArtists (id_song, id_artist) " \
                  f"VALUES ('{track.id}', '{artist.id}')"
            self.cursor.execute(sql)
            self.cursor.reset()

        self.connection.commit()

    def save_album(self, album: Album):
        # insert album
        album_name = album.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Album (id, name, image_url) VALUES " \
              f"('{album.id}', '{album_name}', '{album.image_url}')"
        self.cursor.execute(sql)
        self.cursor.reset()

        for artist in album.artists:
            # insert artists of album
            artist_name = artist.name.replace("'", "\\'")
            sql = f"INSERT IGNORE INTO Artist (id, name) VALUES " \
                  f"('{artist.id}', '{artist_name}')"
            self.cursor.execute(sql)
            self.cursor.reset()

            # link album to artists
            sql = f"INSERT IGNORE INTO AlbumArtists (id_album, id_artist) " \
                  f"VALUES ('{album.id}', '{artist.id}')"
            self.cursor.execute(sql)
            self.cursor.reset()

        # add songs
        for track in album.tracks:
            self.save_song(track)

        self.connection.commit()

    def save_playlist(self, playlist: Playlist):
        # insert playlist
        playlist_name = playlist.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Playlist (id, name) " \
              f"VALUES ('{playlist.id}', '{playlist_name}')"
        self.cursor.execute(sql)
        self.cursor.reset()

        # link playlist tracks
        for track in playlist.tracks:
            # add song
            self.save_song(track)
            # link song and playlist
            sql = f"INSERT IGNORE INTO SongPlaylist (id_song, id_playlist) " \
                  f"VALUES ('{track.id}', '{playlist.id}')"
            self.cursor.execute(sql)
            self.cursor.reset()

        self.connection.commit()

    def get_song(self) -> Track:
        # return future song
        if self.tracks.future_song_exists():
            return self.tracks.get_future_song()

        # return random song
        if not self.tracks.cur_song_exists():
            self.tracks.add_future_track(self.get_random_song())
            return self.tracks.get_future_song()

        cur_track = self.tracks.get_cur_song()

        # get song by album
        self.cursor.execute(f"SELECT id FROM Song "
                            f"WHERE id_album = '{cur_track.album(self).id}' "
                            f"AND id != '{cur_track.id}'")
        for track_id in self.cursor:
            self.cursor.reset()
            self.tracks.add_future_track(
                self._get_song_from_db(track_id[0])
            )
            return self.tracks.get_future_song()
        self.cursor.reset()

        # get song by artist
        for artist in cur_track.artists:
            sql = f"SELECT id_song FROM SongArtists WHERE " \
                  f"id_artist = '{artist.id}' AND id_song != '{cur_track.id}'"
            self.cursor.execute(sql)
            for track_id in self.cursor:
                self.cursor.reset()
                self.tracks.add_future_track(
                    self._get_song_from_db(track_id[0])
                )
                return self.tracks.get_future_song()
            self.cursor.reset()

        # if not song found: return random
        self.tracks.add_future_track(self.get_random_song())
        return self.tracks.get_future_song()

    def get_last_song(self) -> Track:
        if not self.tracks.last_song_exists():
            self.tracks.add_last_track(self.get_random_song())
        return self.tracks.get_last_song()
