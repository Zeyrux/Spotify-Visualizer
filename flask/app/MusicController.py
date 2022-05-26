from pathlib import Path

from mysql import connector


class MusicController:
    def __init__(self, path_database):
        self.path_database = Path(path_database)
        if not self.path_database.is_dir():
            self.path_database.mkdir(parents=True, exist_ok=True)

        self.connection: connector.connection_cext.CMySQLConnection = None
        self.cursor: connector.connection_cext.CMySQLCursor = None

    def _is_existing(self, table: str, id: str) -> bool:
        self.cursor.execute(
            f"SELECT * FROM {table} WHERE id = '{id}'"
        )
        for _ in self.cursor:
            self.cursor.reset()
            return True
        return False

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

    def save_song(self, track: "Track"):
        # insert artists of song
        for artist in track.artists:
            if not self._is_existing("Artist", artist.id):
                sql = f"INSERT INTO Artist (id, name) VALUES " \
                      f"('{artist.id}', '{artist.name}')"
                self.cursor.execute(sql)
                self.cursor.reset()

        # insert song
        if not self._is_existing("Song", track.id):
            sql = f"INSERT INTO Song (id, name) VALUES " \
                  f"('{track.id}', '{track.name}')"
            self.cursor.execute(sql)
            self.cursor.reset()

        # link song to artists
        if not (self._is_existing("Song", track.id)
                and self._is_existing("Artist", track.artists[0].id)):
            for artist in track.artists:
                sql = f"INSERT INTO SongArtists (id_song, id_artist) VALUES " \
                      f"('{track.id}', '{artist.id}')"
                self.cursor.execute(sql)
                self.cursor.reset()

        # insert album
        if not self._is_existing("Album", track.album.id):
            sql = f"INSERT INTO Album(id, name, song_id) VALUES " \
                  f"('{track.album.id}', '{track.album.name}', '{track.id}')"
            self.cursor.execute(sql)
            self.cursor.reset()

        # insert artists of album
        for artist in track.album.artists:
            if not self._is_existing("Artist", artist.id):
                sql = f"INSERT INTO Artist (id, name) VALUES " \
                      f"('{artist.id}', '{artist.name}')"
                self.cursor.execute(sql)
                self.cursor.reset()

        # link album to artists
        if not (self._is_existing("Album", track.album.id)
                and self._is_existing("Artist", track.album.artists[0].id)):
            for artist in track.album.artists:
                sql = f"INSERT INTO AlbumArtists (id_album, id_artist) " \
                      f"VALUES ('{track.album.id}', '{artist.id}')"
                self.cursor.execute(sql)
                self.cursor.reset()

        self.connection.commit()

    def get_song(self, old_track) -> Path:
        pass
