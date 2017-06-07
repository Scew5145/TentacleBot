import json
import sys


# TODO: add basic champion output string / embed and (potentially) embedded videos
class championDB:
    riotKey = ''

    # stat dicts
    def __init__(self, _riotKey):
        self.riotKey = _riotKey

    def pull_bstats(self, championid):
        return

    def get_champstats(self, level):
        # TODO: Implement Stat calc for champion
        statdict = {}
        return statdict

