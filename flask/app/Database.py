import os
import time

from app.SpotifyAPI import Artist, Album, Playlist, Track

from mysql import connector


def execute(conn: "Connection",
            sql: str, fetch_one=False) -> list[tuple] | None:
    conn.cursor.execute(sql, multi=True)
    response = conn.cursor.fetchone() if fetch_one else conn.cursor.fetchall()
    conn.cursor.reset()
    return response


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
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()


class Database:
    def __init__(self, app: "App"):
        self.app = app

    ###########################################################################
    ##################### GET Playlist Album Track Artist #####################
    ###########################################################################

    def get_playlist(self, playlist_id: str, direct_download=False, conn: Connection = None) -> Playlist:
        if conn is None:
            conn = Connection()
        if not self.is_existing("Playlist", playlist_id, conn=conn):
            playlist = self.spotify_api.get_playlist(playlist_id)
            self.save_playlist(
                playlist, direct_download=direct_download, conn=conn)
            return playlist

        sql = f"SELECT name, spotify_url, image_url FROM Playlist " \
              f"WHERE id = '{playlist_id}'"
        playlist_name, spotify_url, image_url = execute(
            conn, sql, fetch_one=True)

        # tracks
        tracks = []
        sql = f"SELECT id_track FROM TrackPlaylist " \
              f"WHERE id_playlist = '{playlist_id}'"
        response = execute(conn, sql)
        for track_id, in response:
            tracks.append(self.get_track(
                track_id, conn=conn))

        return Playlist(playlist_id, playlist_name, spotify_url, tracks, image_url)

    def get_album(self, album_id: str, conn: Connection = None) -> Album:
        if conn is None:
            conn = Connection()
        if not self.is_existing("Album", album_id, conn=conn):
            album = self.app.spotify_api.get_album(album_id)
            self.save_album(album, conn=conn)
            return album

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
                self.get_artist(album_artist_id[0], conn=conn)
            )

        # tracks
        tracks = []
        sql = f"SELECT id FROM Track WHERE id_album = '{album_id}'"
        response = execute(conn, sql)
        for track_id in response:
            tracks.append(self.get_track(track_id[0], conn=conn))

        return Album(
            album_id, album_name, album_spotify_url,
            tracks, album_img_url, album_artists
        )

    def get_track(self, track_id: str, direct_download=False, conn: Connection = None) -> Track:
        if conn is None:
            conn = Connection()
        if not self.is_existing("Track", track_id, conn=conn):
            track = self.downloader.spotify_api.get_track(track_id)
            self.save_track(track, direct_download=direct_download, conn=conn)
            return track

        # track
        sql = f"SELECT name, spotify_url, id_album, duration_ms " \
              f"FROM Track WHERE id = '{track_id}'"
        track_name, spotify_url, album_id, duration_ms = execute(
            conn, sql, fetch_one=True
        )
        # track artists
        artists = []
        sql = f"SELECT id_artist FROM TrackArtists WHERE id_track = '{track_id}'"
        response = execute(conn, sql)
        for artist_id in response:
            artists.append(self.get_artist(artist_id[0], conn=conn))

        return Track(
            track_id, track_name, spotify_url, artists, duration_ms, album_id
        )

    def get_artist(self, artist_id: str, conn: Connection = None) -> Artist:
        if conn is None:
            conn = Connection()
        if not self.is_existing("Artist", artist_id, conn=conn):
            artist = self.app.spotify_api.get_artist(artist_id)
            self.save_artist(artist, conn=conn)
            return artist

        sql = f"SELECT name, spotify_url FROM Artist " \
              f"WHERE id = '{artist_id}'"
        artist_name, artist_spotify_url = execute(conn, sql, fetch_one=True)
        return Artist(artist_id, artist_name, artist_spotify_url)

    ###########################################################################
    ################################ GET OTHER ################################
    ###########################################################################

    def get_random_track(self, conn: Connection = None) -> Track:
        if conn is None:
            conn = Connection()
        sql = "SELECT id FROM Track ORDER BY RAND()"

        while True:
            response = execute(conn, sql, fetch_one=True)
            if response is not None:
                return self.get_track(response[0], conn=conn)
            time.sleep(0.1)

    def get_album_url(self, album_id: str, conn: Connection = None) -> str:
        if conn is None:
            conn = Connection()
        sql = f"SELECT image_url FROM Album WHERE id = '{album_id}'"
        response = execute(conn, sql, fetch_one=True)
        if response is None:
            return response
        return execute(conn, sql, fetch_one=True)[0]

    def get_playlists_from_track(self, track_id: str,
                                 conn: Connection = None) -> list[Playlist]:
        if conn is None:
            conn = Connection()

        if not self.is_existing("Track", track_id, conn=conn):
            track = self.downloader.spotify_api.get_track(track_id)
            self.save_track(track, conn=conn)

        playlists = []
        sql = f"SELECT id_playlist FROM TrackPlaylist " \
              f"WHERE id_track = '{track_id}'"
        response = execute(conn, sql)
        for playlist_id in response:
            playlists.append(self.get_playlist(playlist_id[0], conn=conn))
        return playlists

    ##########################################################################
    ################################# EXISTS #################################
    ##########################################################################

    def playlist_exists(self, playlist: Playlist, conn: Connection = None) -> bool:
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

    def tracks_exists(self, super: Playlist | Album,
                      conn: Connection = None) -> bool:
        if conn is None:
            conn = Connection()
        super_name = type(super).__name__

        # check every track
        for track in super.tracks:
            # check if track exists
            if not self.track_exists(track.id) \
                    or not os.path.isfile(os.path.join(self.DATABASE_DIR,
                                                       track.id_filename)):
                return False
            # link tracks
            sql = f"INSERT IGNORE INTO Track{super_name} " \
                f"(id_track, id_{super_name}) " \
                f"VALUES ('{track.id}', '{super.id}')"
            execute(conn, sql)
        return True

    def track_exists(self, track: Track, conn: Connection = None) -> bool:
        if conn is None:
            conn = Connection()
        if not self.is_existing("Track", track.id, conn=conn):
            return False
        for artist in track.artists:
            if not self.artist_exists(artist, conn=conn):
                return False
            sql = f"INSERT IGNORE INTO TrackArtists " \
                f"(id_track, id_artist) " \
                f"VALUES ('{track.id}', '{artist.id}')"
            execute(conn, sql)
        return True

    def artist_exists(self, artist: Artist, conn: Connection = None) -> bool:
        if conn is None:
            conn = Connection()
        return self.is_existing("Artist", artist.id, conn=conn)

    def is_existing(self, table: str, id: str,
                    conn: Connection = None) -> bool:
        if conn is None:
            conn = Connection()
        sql = f"SELECT * FROM {table} WHERE id = '{id}'"
        exists = False if execute(conn, sql, fetch_one=True) is None else True
        return exists

    ##########################################################################
    ################################## SAVE ##################################
    ##########################################################################

    def save_playlist(self, playlist: Playlist, force_insert: bool = False,
                      direct_download=False, conn: Connection = None):
        if conn is None:
            conn = Connection()
        if not force_insert:
            if self.is_existing("Playlist", playlist.id, conn=conn):
                return

        # save playlist
        playlist_name = playlist.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Playlist (id, name, spotify_url, image_url)" \
              f" VALUES ('{playlist.id}', '{playlist_name}', " \
              f"'{playlist.spotify_url}', '{playlist.image_url}')"
        execute(conn, sql)

        # save tracks
        for track in playlist.tracks:
            self.save_track(track, force_insert=force_insert,
                            direct_download=direct_download, conn=conn)

        # link tracks
        for track in playlist.tracks:
            sql = f"INSERT IGNORE INTO TrackPlaylist " \
                  f"(id_track, id_playlist) " \
                  f"VALUES ('{track.id}', '{playlist.id}')"
            execute(conn, sql)

    def save_album(self, album: Album, force_insert: bool = False, conn: Connection = None):
        if conn is None:
            conn = Connection()
        if not force_insert:
            if self.is_existing("Album", album.id, conn=conn):
                return

        # save album
        album_name = album.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Album (id, name, spotify_url, image_url) " \
              f"VALUES ('{album.id}', '{album_name}', " \
              f"'{album.spotify_url}', '{album.image_url}')"
        execute(conn, sql)

        # save album artists
        for artist in album.artists:
            self.save_artist(artist, force_insert=force_insert, conn=conn)

        # link album to artists
        for artist in album.artists:
            sql = f"INSERT IGNORE INTO AlbumArtists (id_album, id_artist) " \
                  f"VALUES ('{album.id}', '{artist.id}')"
            execute(conn, sql)

        # save album tracks
        for track in album.tracks:
            self.save_track(track, force_insert=force_insert, conn=conn)

    def save_track(self, track: Track, force_insert: bool = False, direct_download=False, conn: Connection = None):
        if conn is None:
            conn = Connection()
        if not force_insert:
            if self.is_existing("Track", track.id, conn=conn) \
                    and os.path.isfile(os.path.join(self.app.DATABASE_DIR, track.id_filename)):
                return
        if not os.path.isfile(os.path.join(self.app.DATABASE_DIR, track.id_filename)):
            if direct_download:
                self.app.downloader.download_track(track)
            else:
                self.app.downloader.put_queue(track)

        # save track
        track_name = track.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Track " \
              f"(id, name, spotify_url, id_album, duration_ms) VALUES " \
              f"('{track.id}', '{track_name}', '{track.spotify_url}', " \
              f"'{track.id_album}', '{track.duration_ms}')"
        execute(conn, sql)

        # save track artists
        for artist in track.artists:
            self.save_artist(artist, force_insert=force_insert, conn=conn)

        # link track to artists
        for artist in track.artists:
            sql = f"INSERT IGNORE INTO TrackArtists (id_track, id_artist) " \
                  f"VALUES ('{track.id}', '{artist.id}')"
            execute(conn, sql)

        # save album
        if not force_insert:
            if self.is_existing("Album", track.id_album, conn=conn):
                return
        self.save_album(
            track.album(self), conn=conn)

    def save_artist(self, artist: Artist, force_insert: bool = False, conn: Connection = None):
        if conn is None:
            conn = Connection()
        if not force_insert:
            if not self.is_existing("Artist", artist.id, conn=conn):
                return

        # save artist
        artist_name = artist.name.replace("'", "\\'")
        sql = f"INSERT IGNORE INTO Artist (id, name, spotify_url) " \
            f"VALUES ('{artist.id}', '{artist_name}', " \
            f"'{artist.spotify_url}')"
        execute(conn, sql)
