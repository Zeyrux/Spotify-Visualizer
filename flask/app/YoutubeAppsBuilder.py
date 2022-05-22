import os

from googleapiclient.discovery import build


class YoutubeAppsBuilder:
    def __init__(self, keys_path):
        self.keys_path = keys_path
        self.apps = []
        for key in open(keys_path, "r").readlines():
            self.apps.append(build("youtube",
                                   "v3",
                                   developerKey=key.replace("\n", "")))
        self.cur_app = -1

    def get_app(self) -> str:
        self.cur_app += 1
        return self.apps[self.cur_app % len(self.apps)]

    def __len__(self):
        return len(self.apps)