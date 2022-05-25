from pathlib import Path

from mysql import connector


class MusicController:
    def __init__(self, path_database):
        self.path_database = Path(path_database)
        if not self.path_database.is_dir():
            self.path_database.mkdir(parents=True, exist_ok=True)

        self.connection: connector.connection_cext.CMySQLConnection = None

    def connect(self):
        config = {
            'user': 'root',
            'password': 'root',
            'host': 'database',
            'port': '3306',
            'database': 'Music'
        }
        self.connection = connector.connect(**config)

    def get_song(self, old_track) -> Path:
        pass