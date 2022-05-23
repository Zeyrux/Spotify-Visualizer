from pathlib import Path


class MusicController:
    def __init__(self, path_database):
        self.path_database = Path(path_database)
        if not self.path_database.is_dir():
            self.path_database.mkdir(parents=True, exist_ok=True)
