import json
import sys
import requests



class championDB:
    # Class for handling riot static API requests and doing level based calcs.

    riotKey = ''

    # stat dicts don't need to be loaded permanently because there's no limit on static requests! Yay!
    def __init__(self, _riotKey):
        self.riotKey = _riotKey

    def get_champId(self, championName):
        # helper fuction for converting name -> id for api requests.
        # -1 means bad champion name. -2 means bad url retrieval.
        # Pulls from this: https://developer.riotgames.com/api-methods/#lol-static-data-v3/GET_getChampionList
        id = -1
        url = 'https://na1.api.riotgames.com/lol/static-data/v3/champions'
        url += '?api_key='
        url += self.riotKey

        response = requests.get(url)
        if response.status_code != 200:
            print('something went wrong with retrieving the id.')
            print('Error code: ', response.status_code)
            return -2
        champData = json.loads(response.text)
        for champion in champData:
            if champion['name'].lower() == championName.lower():
                id = champion['id']

        if id == -1:
            print("Couldn't find champion " + championName + '.')
        return id

    def get_bstats(self, championid):
        url = 'https://na1.api.riotgames.com/lol/static-data/v3/champions/'
        url += str(id)
        # TODO: update URL when server is back up so testing can happen
        url += '?champData=stats&api_key='
        url += self.riotKey
        response = requests.get(url)
        # handling status code errors outside of the dict. If we don't receive a good response, pass it out.
        # This is so custom error messages can be used based on the context. Ex: Discord message vs print()
        if response.status_code != 200:
            return {'statuscode' : response.status_code}

        statDict = json.loads(response.text)
        statDict.update({'statuscode' : response.status_code})
        # If the statDict is good, stat names can be found here:
        # https://developer.riotgames.com/api-methods/#lol-static-data-v3/GET_getChampionById
        return statDict

    def get_levelinfo(self, level, id):
        # TODO: Implement Stat calc for champion
        statdict = {}
        return statdict

