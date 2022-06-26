import time
import os
from threading import Thread
from queue import Queue
from pathlib import Path

from app.SpotifyAPI import Artist, Album, Playlist, Track

from mysql import connector


def execute(conn: "Connection", sql: str, fetch_one=False) -> list[tuple]:
    print(sql)
    response = conn.cursor.execute(sql, multi=True)
    # response = conn.cursor.stored_results()
    conn.cursor.reset()
    return response[0] if fetch_one else response
# SELECT doesn´t work!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


class Tracks:
    def __init__(self):
        self.tracks = []
        self.cur_track = -1

    def __str__(self):
        return f"Tracks(pt: {self.cur_track}, tracks: " \
               f"[{','.join([track.name for track in self.tracks])}])"

    def add_next_track(self, track: Track):
        self.tracks.insert(self.cur_track + 1, track)

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


class Connection:
    def __init__(self, user: str):
        config = {
            "user": user,
            "password": "root",
            # "host": "database",
            "host": "localhost",
            "port": "3306",
            "database": "Music"
        }
        self.connection = connector.connect(**config)
        self.cursor = self.connection.cursor()

        self.cursor.execute("SET GLOBAL log_output = 'FILE'")
        self.cursor.reset()
        self.cursor.execute("SET GLOBAL general_log = 'ON'")
        self.cursor.reset()


class MusicController:
    def __init__(self, path_database: Path):
        self.path_database = path_database
        if not self.path_database.is_dir():
            self.path_database.mkdir(parents=True, exist_ok=True)
        self.tracks = Tracks()

        self.conn = Connection("root")
        self.downloader: "MusicDownloader" | None = None
        self.queue = Queue()
        self.download_thread = Thread(target=self._worker_save_song,
                                      daemon=True)
        self.download_thread.start()

    def get_song_from_db(self, song_id, conn: Connection = None) -> Track:
        if conn is None:
            conn = self.conn
        # create song if not existing
        if not self.is_existing("Song", song_id):
            track = self.downloader.spotify_api.get_track()
            self.save_song(track)
            return track
        # song
        sql = f"SELECT name, id_album, duration_ms " \
              f"FROM Song WHERE id = '{song_id}'"
        song_name, album_id, duration_ms = execute(conn, sql, fetch_one=True)

        # song artists
        artists = []
        sql = f"SELECT id_artist FROM SongArtists WHERE id_song = '{song_id}'"
        response = execute(conn, sql)
        for artist_id in response:
            sql = f"SELECT name FROM Artist WHERE id = '{artist_id[0]}'"
            artist_name = execute(conn, sql, fetch_one=True)
            artists.append(Artist(artist_id[0], artist_name[0]))

        return Track(
            song_id, song_name, artists, duration_ms, album_id
        )

    def is_existing(self, table: str, id: str,
                    conn: Connection = None) -> bool:
        if conn is None:
            conn = self.conn
        sql = f"SELECT * FROM {table} WHERE id = '{id}'"
        exists = False if execute(conn, sql, fetch_one=True) is None else True
        return exists

    def get_playlist(self, playlist_id: str,
                     conn: Connection = None) -> Playlist:
        if conn is None:
            conn = self.conn

        if not self.is_existing("Playlist", playlist_id):
            playlist = self.downloader.spotify_api.get_playlist(playlist_id)
            self.save_playlist(playlist)

        sql = f"SELECT name FROM Playlist WHERE id = '{playlist_id}'"
        playlist_name, = execute(conn, sql, fetch_one=True)

        # songs
        songs = []
        sql = f"SELECT id_song FROM Playlist " \
              f"WHERE id_playlist = '{playlist_id}'"
        response = execute(conn, sql)
        for song_id in response:
            songs.append(self.get_song_from_db(song_id))

        return Playlist(playlist_id, playlist_name, songs)

    def get_album(self, album_id: str, conn: Connection = None) -> Album:
        if conn is None:
            conn = self.conn

        if not self.is_existing("Album", album_id):
            album = self.downloader.spotify_api.get_album(album_id)
            self.save_album(album)

        sql = f"SELECT name, image_url FROM Album WHERE id = '{album_id}'"
        album_name, album_img_url = execute(conn, sql, fetch_one=True)

        # album artists
        album_artists = []
        sql = f"SELECT id_artist FROM AlbumArtists " \
              f"WHERE id_album = '{album_id}'"
        response = execute(conn, sql)
        for album_artist_id in response:
            sql = f"SELECT * FROM Artist WHERE id = '{album_artist_id[0]}'"
            album_artist = execute(conn, sql, fetch_one=True)
            album_artists.append(Artist(album_artist[0], album_artist[1]))

        # songs
        songs = []
        sql = f"SELECT id FROM Song WHERE id_album = '{album_id}'"
        response = execute(conn, sql)
        for song_id in response:
            songs.append(self.get_song_from_db(song_id[0]))

        return Album(
            album_id, album_name, songs, album_img_url, album_artists
        )

    def get_playlists_from_track(self, track_id: str,
                                 conn: Connection = None) -> list[Playlist]:
        if conn is None:
            conn = self.conn

        if not self.is_existing("Song", track_id):
            track = self.downloader.spotify_api.get_track(track_id)
            self.save_song(track)

        playlists = []
        sql = f"SELECT id_playlist FROM SongPlaylist " \
              f"WHERE id_song = '{track_id}'"
        response = execute(conn, sql)
        for playlist_id in response:
            playlists.append(self.get_playlist(playlist_id))
        return playlists

    def get_random_song(self, conn: Connection = None) -> Track:
        if conn is None:
            conn = self.conn

        sql = f"SELECT id FROM Song ORDER BY RAND()"
        response = execute(conn, sql)
        for track_id in response:
            return self.get_song_from_db(track_id[0])

        # if not song exists in database, wait until one is added
        time.sleep(2)
        return self.get_random_song()

    def _worker_save_song(self):
        conn = Connection("root")
        while True:
            track, add_future_tracks = self.queue.get()
            self._save_song(track, add_future_tracks, conn=conn)
            self.queue.task_done()

    def save_song(self, track: Track, add_future_tracks=False, threaded=False):
        if threaded:
            self.queue.put((track, add_future_tracks))
        else:
            self._save_song(track, add_future_tracks)

    def _save_song(self, track: Track, add_future_tracks,
                   conn: Connection = None):
        if conn is None:
            conn = self.conn

        if not os.path.isfile(os.path.join(self.downloader.song_dir,
                                           track.id_filename)):
            self.downloader.download_song(track)

        # refresh cur, last track
        if add_future_tracks:
            self.tracks.add_future_track(track)

        # insert artists of song
        for artist in track.artists:
            artist_name = artist.name.replace("'", "\\'")
            sql = f"INSERT IGNORE INTO Artist (id, name) VALUES " \
                  f"('{artist.id}', '{artist_name}')"
            execute(conn, sql)

        # insert song
        track_name = track.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Song " \
              f"(id, name, id_album, duration_ms) VALUES " \
              f"('{track.id}', '{track_name}', " \
              f"'{track.id_album}', '{track.duration_ms}')"
        execute(conn, sql)

        # link song to artists
        for artist in track.artists:
            sql = f"INSERT IGNORE INTO SongArtists (id_song, id_artist) " \
                  f"VALUES ('{track.id}', '{artist.id}')"
            execute(conn, sql)

        conn.connection.commit()

    def save_album(self, album: Album, threaded=False,
                   conn: Connection = None):
        if conn is None:
            conn = self.conn

        # insert album
        album_name = album.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Album (id, name, image_url) VALUES " \
              f"('{album.id}', '{album_name}', '{album.image_url}')"
        execute(conn, sql)

        for artist in album.artists:
            # insert artists of album
            artist_name = artist.name.replace("'", "\\'")
            sql = f"INSERT IGNORE INTO Artist (id, name) VALUES " \
                  f"('{artist.id}', '{artist_name}')"
            execute(conn, sql)

            # link album to artists
            sql = f"INSERT IGNORE INTO AlbumArtists (id_album, id_artist) " \
                  f"VALUES ('{album.id}', '{artist.id}')"
            execute(conn, sql)

        # add songs
        for track in album.tracks:
            self.save_song(track, threaded=threaded)

        conn.connection.commit()

    def save_playlist(self, playlist: Playlist, threaded=False,
                      conn: Connection = None):
        if conn is None:
            conn = self.conn

        # insert playlist
        playlist_name = playlist.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Playlist (id, name) " \
              f"VALUES ('{playlist.id}', '{playlist_name}')"
        execute(conn, sql)

        # link playlist tracks
        for track in playlist.tracks:
            # add song
            self.save_song(track, threaded=threaded)
            # link song and playlist
            sql = f"INSERT IGNORE INTO SongPlaylist (id_song, id_playlist) " \
                  f"VALUES ('{track.id}', '{playlist.id}')"
            execute(conn, sql)

        conn.connection.commit()

    def get_song(self, conn: Connection = None) -> Track:
        if conn is None:
            conn = self.conn

        # return future song
        if self.tracks.future_song_exists():
            return self.tracks.get_future_song()

        # return random song
        if not self.tracks.cur_song_exists():
            self.tracks.add_future_track(self.get_random_song())
            return self.tracks.get_future_song()

        cur_track = self.tracks.get_cur_song()

        # get song by album
        sql = f"SELECT id FROM Song WHERE id_album = " \
              f"'{cur_track.album(self).id}' AND id != '{cur_track.id}'"
        response = execute(conn, sql)
        for track_id in response:
            self.tracks.add_future_track(
                self.get_song_from_db(track_id[0])
            )
            return self.tracks.get_future_song()

        # get song by artist
        for artist in cur_track.artists:
            sql = f"SELECT id_song FROM SongArtists WHERE " \
                  f"id_artist = '{artist.id}' AND id_song != '{cur_track.id}'"
            response = execute(conn, sql)
            for track_id in response:
                self.tracks.add_future_track(
                    self.get_song_from_db(track_id[0])
                )
                return self.tracks.get_future_song()

        # if not song found: return random
        self.tracks.add_future_track(self.get_random_song())
        return self.tracks.get_future_song()

    def get_last_song(self) -> Track:
        if not self.tracks.last_song_exists():
            self.tracks.add_last_track(self.get_random_song())
        return self.tracks.get_last_song()
