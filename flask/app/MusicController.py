import time
import os
from threading import Thread
from queue import Queue
from pathlib import Path

from app.SpotifyAPI import Artist, Album, Playlist, Track

from mysql import connector


def execute(conn: "Connection",
            sql: str, fetch_one=False) -> list[tuple] | None:
    conn.cursor.execute(sql, multi=True)
    response = conn.cursor.fetchone() if fetch_one else conn.cursor.fetchall()
    conn.cursor.reset()
    return response


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
    def __init__(self):
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


class MusicController:
    def __init__(self, path_database: Path):
        self.path_database = path_database
        if not self.path_database.is_dir():
            self.path_database.mkdir(parents=True, exist_ok=True)
        self.tracks = Tracks()

        self.conn = Connection()
        self.downloader: "MusicDownloader" | None = None
        self.queue = Queue()
        self.download_thread = Thread(target=self._worker_save_song,
                                      daemon=True)
        self.download_thread.start()

    def get_song_from_db(self, song_id, conn: Connection = None) -> Track:
        if conn is None:
            conn = Connection()
        # create song if not existing
        if not self.is_existing("Song", song_id, conn=conn):
            track = self.downloader.spotify_api.get_track()
            self.save_song(track, conn=conn)
            return track
        # song
        sql = f"SELECT name, spotify_url, id_album, duration_ms " \
              f"FROM Song WHERE id = '{song_id}'"
        song_name, spotify_url, album_id, duration_ms = execute(
            conn, sql, fetch_one=True
        )

        # song artists
        artists = []
        sql = f"SELECT id_artist FROM SongArtists WHERE id_song = '{song_id}'"
        response = execute(conn, sql)
        for artist_id in response:
            artists.append(self.get_artists_from_db(artist_id[0], conn=conn))

        return Track(
            song_id, song_name, spotify_url, artists, duration_ms, album_id
        )

    def get_artists_from_db(self, artist_id: str,
                            conn: Connection = None) -> Artist:
        if conn is None:
            conn = Connection()
        sql = f"SELECT name, spotify_url FROM Artist " \
              f"WHERE id = '{artist_id}'"
        artist_name, artist_spotify_url = execute(conn, sql, fetch_one=True)
        return Artist(artist_id, artist_name, artist_spotify_url)

    def is_existing(self, table: str, id: str,
                    conn: Connection = None) -> bool:
        if conn is None:
            conn = Connection()
        sql = f"SELECT * FROM {table} WHERE id = '{id}'"
        exists = False if execute(conn, sql, fetch_one=True) is None else True
        return exists

    def tracks_exists(self, super: Playlist | Album,
                      conn: Connection = None) -> bool:
        if conn is None:
            conn = Connection()
        super_name = type(super).__name__

        # check every track
        for track in super.tracks:
            if not self.is_existing("Song", track.id, conn=conn):
                # check if song exists
                return False
            else:
                # check if song is linked
                sql = f"SELECT * FROM Song{super_name} " \
                      f"WHERE id_song = '{track.id}' AND " \
                      f"id_{super_name} = '{super.id}'"
                if execute(conn, sql, fetch_one=True) is None:
                    sql = f"INSERT IGNORE INTO Song{super_name} " \
                          f"(id_song, id_{super_name}) " \
                          f"VALUES ('{track.id}', '{super.id}')"
                    execute(conn, sql)
        return True

    def playlist_exists(self, playlist: Playlist,
                        conn: Connection = None) -> bool:
        if conn is None:
            conn = Connection()
        if not self.is_existing("Playlist", playlist.id, conn=conn):
            return False
        return self.tracks_exists(playlist, conn=conn)

    def album_exists(self, album: Album, conn: Connection = None):
        if conn is None:
            conn = Connection()
        if not self.is_existing("Album", album.id, conn=conn):
            return False
        return self.tracks_exists(album, conn)

    def get_playlist(self, playlist_id: str,
                     conn: Connection = None) -> Playlist:
        if conn is None:
            conn = Connection()

        if not self.playlist_exists("Playlist", playlist_id, conn=conn):
            playlist = self.downloader.spotify_api.get_playlist(playlist_id)
            self.save_playlist(playlist, conn=conn)

        sql = f"SELECT name, spotify_url FROM Playlist " \
              f"WHERE id = '{playlist_id}'"
        playlist_name, spotify_url = execute(conn, sql, fetch_one=True)

        # songs
        songs = []
        sql = f"SELECT id_song FROM Playlist " \
              f"WHERE id_playlist = '{playlist_id}'"
        response = execute(conn, sql)
        for song_id in response:
            songs.append(self.get_song_from_db(song_id, conn=conn))

        return Playlist(playlist_id, playlist_name, spotify_url, songs)

    def get_album(self, album_id: str, conn: Connection = None) -> Album:
        if conn is None:
            conn = Connection()

        if not self.is_existing("Album", album_id, conn=conn):
            album = self.downloader.spotify_api.get_album(album_id)
            self.save_album(album, conn=conn)

        sql = f"SELECT name, spotify_url, image_url FROM Album " \
              f"WHERE id = '{album_id}'"
        album_name, album_spotify_url, album_img_url = execute(
            conn, sql, fetch_one=True
        )

        # album artists
        album_artists = []
        sql = f"SELECT id_artist FROM AlbumArtists " \
              f"WHERE id_album = '{album_id}'"
        response = execute(conn, sql)
        for album_artist_id in response:
            album_artists.append(
                self.get_artists_from_db(album_artist_id[0], conn=conn)
            )

        # songs
        songs = []
        sql = f"SELECT id FROM Song WHERE id_album = '{album_id}'"
        response = execute(conn, sql)
        for song_id in response:
            songs.append(self.get_song_from_db(song_id[0], conn=conn))

        return Album(
            album_id, album_name, album_spotify_url,
            songs, album_img_url, album_artists
        )

    def get_playlists_from_track(self, track_id: str,
                                 conn: Connection = None) -> list[Playlist]:
        if conn is None:
            conn = Connection()

        if not self.is_existing("Song", track_id, conn=conn):
            track = self.downloader.spotify_api.get_track(track_id)
            self.save_song(track, conn=conn)

        playlists = []
        sql = f"SELECT id_playlist FROM SongPlaylist " \
              f"WHERE id_song = '{track_id}'"
        response = execute(conn, sql)
        for playlist_id in response:
            playlists.append(self.get_playlist(playlist_id[0], conn=conn))
        return playlists

    def get_random_song(self, conn: Connection = None) -> Track:
        if conn is None:
            conn = Connection()
        sql = f"SELECT id FROM Song ORDER BY RAND()"

        while True:
            response = execute(conn, sql)
            for track_id in response:
                return self.get_song_from_db(track_id[0], conn=conn)

            # if not song exists in database, wait until one is added
            time.sleep(2)

    def _worker_save_song(self):
        conn = Connection()
        while True:
            track, add_future_tracks = self.queue.get()
            self._save_song(track, add_future_tracks, conn=conn)
            self.queue.task_done()

    def save_song(self, track: Track, add_future_tracks=False,
                  threaded=False, conn: Connection = None):
        if conn is None:
            conn = Connection()
        if self.is_existing("Song", track.id, conn=conn):
            return
        if threaded:
            self.queue.put((track, add_future_tracks))
        else:
            self._save_song(track, add_future_tracks, conn=conn)

    def _save_song(self, track: Track, add_future_tracks,
                   conn: Connection = None):
        if conn is None:
            conn = Connection()

        if not os.path.isfile(os.path.join(self.downloader.song_dir,
                                           track.id_filename)):
            self.downloader.download_song(track)

        # refresh cur, last track
        if add_future_tracks:
            self.tracks.add_future_track(track)

        track_album_id = self.downloader.spotify_api.get_album_id_of_track(
            track.id
        )
        if not self.is_existing("Album", track_album_id, conn=conn):
            self.save_album(
                self.downloader.spotify_api.get_album(track_album_id),
                conn=conn
            )

        # insert artists of song
        for artist in track.artists:
            artist_name = artist.name.replace("'", "\\'")
            sql = f"INSERT IGNORE INTO " \
                  f"Artist (id, name, spotify_url) VALUES " \
                  f"('{artist.id}', '{artist_name}', '{artist.spotify_url}')"
            execute(conn, sql)

        # insert song
        track_name = track.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Song " \
              f"(id, name, spotify_url, id_album, duration_ms) VALUES " \
              f"('{track.id}', '{track_name}', '{track.spotify_url}', " \
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
            conn = Connection()
        if self.album_exists(album, conn=conn):
            return

        # insert album
        album_name = album.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Album (id, name, spotify_url, image_url) " \
              f"VALUES ('{album.id}', '{album_name}', " \
              f"'{album.spotify_url}', '{album.image_url}')"
        execute(conn, sql)

        for artist in album.artists:
            # insert artists of album
            artist_name = artist.name.replace("'", "\\'")
            sql = f"INSERT IGNORE INTO Artist (id, name, spotify_url) VALUES " \
                  f"('{artist.id}', '{artist_name}', '{artist.spotify_url}')"
            execute(conn, sql)

            # link album to artists
            sql = f"INSERT IGNORE INTO AlbumArtists (id_album, id_artist) " \
                  f"VALUES ('{album.id}', '{artist.id}')"
            execute(conn, sql)

        conn.connection.commit()

        # add songs
        for track in album.tracks:
            self.save_song(track, threaded=threaded, conn=conn)

    def save_playlist(self, playlist: Playlist, threaded=False,
                      conn: Connection = None):
        if conn is None:
            conn = Connection()
        if self.playlist_exists(playlist, conn=conn):
            return

        # insert playlist
        playlist_name = playlist.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Playlist (id, name, spotify_url) VALUES " \
              f"('{playlist.id}', '{playlist_name}', '{playlist.spotify_url}')"
        execute(conn, sql)

        # link playlist tracks
        for track in playlist.tracks:
            # add song
            self.save_song(track, threaded=threaded, conn=conn)
            # link song and playlist
            sql = f"INSERT IGNORE INTO SongPlaylist (id_song, id_playlist) " \
                  f"VALUES ('{track.id}', '{playlist.id}')"
            execute(conn, sql)

        conn.connection.commit()

    def get_song(self, conn: Connection = None) -> Track:
        if conn is None:
            conn = Connection()

        # return future song
        if self.tracks.future_song_exists():
            return self.tracks.get_future_song()

        # return random song
        if not self.tracks.cur_song_exists():
            self.tracks.add_future_track(self.get_random_song(conn=conn))
            return self.tracks.get_future_song()

        cur_track = self.tracks.get_cur_song()

        # get song by album
        sql = f"SELECT id FROM Song WHERE id_album = " \
              f"'{cur_track.album(self).id}' AND id != '{cur_track.id}'"
        response = execute(conn, sql)
        for track_id in response:
            self.tracks.add_future_track(
                self.get_song_from_db(track_id[0], conn=conn)
            )
            return self.tracks.get_future_song()

        # get song by artist
        for artist in cur_track.artists:
            sql = f"SELECT id_song FROM SongArtists WHERE " \
                  f"id_artist = '{artist.id}' AND id_song != '{cur_track.id}'"
            response = execute(conn, sql)
            for track_id in response:
                self.tracks.add_future_track(
                    self.get_song_from_db(track_id[0], conn=conn)
                )
                return self.tracks.get_future_song()

        # if not song found: return random
        self.tracks.add_future_track(self.get_random_song(conn=conn))
        return self.tracks.get_future_song()

    def get_last_song(self, conn: Connection = None) -> Track:
        if conn is None:
            conn = Connection()
        if not self.tracks.last_song_exists():
            self.tracks.add_last_track(self.get_random_song(conn=conn))
        return self.tracks.get_last_song()
