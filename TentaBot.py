import discord
import json
import random
import requests
import asyncio
import sys
import os

raw = ''
discToken = ''
riotKey = ''
regions = ['NA1', 'RU', 'KR', 'EUN1', 'EUW1', 'TR1', 'LA1', 'LA2', 'BR1', 'OC1', 'JP1']
if len(sys.argv) == 1:
    riotKey = os.environ.get('RIOTKEY')
    discToken = os.environ.get('DISCKEY')
else:
    print('usage: TentaBot.py')
    exit()
print(riotKey, 'riotkey', discToken)



client = discord.Client()
random.seed(None)
with open('insults.json') as insultfile:
    insultDict = json.load(insultfile)


def pull_sum_ID(username, server = 'NA1'):
    # Uses the Riot API to grab the account's ID and return it. Doesn't return region, as it's an input.
    if server.upper() in ['EUN', 'EUW', 'TR', 'BR', 'OC', 'NA', 'JP']:
        server += '1'
    elif server.upper() in ['EUNE', 'EUNE1']:
        server = 'EUN1'
    if server.upper() not in regions:
        print('bad region. Please provide valid region id.')
        return -1
    url = 'https://'
    url += server
    url += '.api.riotgames.com/lol/summoner/v3/summoners/by-name/'
    url += username
    url += '?api_key='
    url += riotKey
    response = requests.get(url)
    if response.status_code != 200:
        print('something went wrong with the request. \n Status Code:', response.status_code)
        return -1
    accDict = json.loads(response.text)
    # print(accDict)
    return accDict['accountId'], accDict['id']


def has_fed(acc_id, server = 'NA1'):
    # Grabs KDA from most recent game, cs delta, win/loss.
    # Total riotAPI Requests inside code: 2
    if server.upper() in ['EUN', 'EUW', 'TR', 'BR', 'OC', 'NA', 'JP']:
        server += '1'
    elif server.upper() in ['EUNE', 'EUNE1']:
        server = 'EUN1'
    if server.upper() not in regions:
        print('bad region. Please provide valid region id.')
        return -1

    # Match History (20 Entries)
    url = 'https://'
    url += server
    url += '.api.riotgames.com/lol/match/v3/matchlists/by-account/'
    url += str(acc_id)
    url += '/recent?api_key='
    url += riotKey

    response = requests.get(url)
    if response.status_code == 404:
        return "Couldn't find recent games for user provided on server" + server
    elif response.status_code != 200:
        print('something went wrong with the request. \n Status Code:', response.status_code)
        return "Something is broken loading match history and I don't know what: " + response.status_code
    recent_games = json.loads(response.text)
    most_recent_match_id = -1
    for match in recent_games['matches']:
        if match['queue'] == 420:
            most_recent_match_id = match['gameId']
            break

    if most_recent_match_id == -1:
        return "No ranked match in the last 20 games. Normals and stuff are private so I can't do things with them."


    # Most Recent Match Overview
    url = 'https://'
    url += server
    url += '.api.riotgames.com/lol/match/v3/matches/'
    url += str(most_recent_match_id)
    url += '?api_key='
    url += riotKey
    response = requests.get(url)
    if response.status_code != 200:
        print('something went wrong with the request. \n Status Code:', response.status_code)
        return "Something is broken loading the most recent game and I don't know what: " + response.status_code
    gameDict = json.loads(response.text)

    parid = -1
    for entry in gameDict['participantIdentities']:
        if entry['player']['accountId'] == acc_id:
            parid = entry['participantId']
            break
    if parid == -1 :
        return "Couldn't find parid. something is super broken."


    playerdata = {}
    enemydata = {}
    for participant in gameDict['participants']:
        if participant['participantId'] == parid:
            playerdata = {
                'kills': participant['stats']['kills'],
                'deaths': participant['stats']['deaths'],
                'assists': participant['stats']['assists'],
                'win': participant['stats']['win'],
                'csdelta': participant['timeline']['creepsPerMinDeltas'],
                'golddelta': participant['timeline']['goldPerMinDeltas'],
                'xpdelta': participant['timeline']['xpDiffPerMinDeltas'],
                'lane': participant['timeline']['lane'],
                'role': participant['timeline']['role']
            }
            break
    for participant in gameDict['participants']: #have to go through the whole dictionary to find the right opponent.

        if (participant['timeline']['lane'] == playerdata['lane']) and (parid != participant['participantId']):
            if participant['timeline']['role'] == playerdata['role']:
                enemydata = {
                    "kills": participant['stats']['kills'],
                    "deaths": participant['stats']['deaths'],
                    "assists": participant['stats']['assists']
                }
                break

    #Print statement for bot output:
    output = ''
    feeder = True
    kda = round((playerdata['kills'] + playerdata['assists']) / playerdata['deaths'], 2)
    enemykda = round((enemydata['kills'] + enemydata['assists']) / enemydata['deaths'],2)

    kdadiff = kda - enemykda
    if playerdata['win']:
        output += 'USER won their last ranked game! \n'
    else:
        output += 'USER fucked up last ranked game. \n'
    if kda < 1.0:
        output += "They had a negative KDA of "
    else:
        output += "They had a positive KDA of "
    output += str(kda) + '.\n'
    output += 'At 10 Minutes, they had a CS difference with their opponent of ' + str(round(playerdata['csdelta']['0-10'],2))
    output += ',\n a Gold difference of ' + str(round(playerdata['golddelta']['0-10'],2)) + ',\n'
    output += 'and a XP difference of ' + str(round(playerdata['xpdelta']['0-10'],2)) + '.\n'
    if kda < 1.0:
        if playerdata['golddelta']['0-10'] > 0.0:
            output += 'They sort of fed, as they were ahead on gold but had a negative kda. '
        elif playerdata['golddelta']['0-10'] < 0.0:
            output += 'the player was a feeder, as their KDA was negative and they were behind on gold. '
        if kda > enemykda:
            output += 'That said, their opponent sucked more. The enemy laner had a KDA of ' + str(enemykda) + '.\n'
        else:
            output += 'Their opponent beat them with a kda of ' + str(enemykda) + '.\n'
    if kda > 1.0:
        if playerdata['golddelta']['0-10'] > 0.0:
            output += 'The player was quite ahead. They had a positive KDA and were ahead on gold. \n'
        elif playerdata['golddelta']['0-10'] < 0.0:
            output += 'The USER was stuck in ELO hell, as they had a positive KDA but were behind on gold. \n'
        if kda > enemykda:
            output += 'The enemy was shit, with a KDA of ' + str(enemykda) + '.\n'
        else:
            output += 'Both '+ playerdata['lane'] + 'players were fed, but the enemy was fatter with a KDA of '
            output += str(enemykda) + '.\n'
        output += "That's a KDA difference of " + str(round(kdadiff,2)) + ". "
    return output



@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

questionBlacklist = []
@client.event
async def on_message(message):
    if message.author != client.user:

        if message.content.startswith('!ping'): #Repeats what the user says
                await client.send_message(message.channel, message.content)

        if message.content.startswith('!8ball'):
            if len(message.content) > 7:
                random.seed(message.author.name.join(message.content[6:]))
            else:
                await client.send_message(message.channel, "How am I supposed to answer a question that doesn't exist?")
                return
            ballreplies = [
                "Yes.",
                "No.",
                "Maybe?",
                "Dude why ask me I'm a tentacle not a prophet literally all I do is smash whoever people tell me to",
                "Probably, if you're dumb enough.",
                "I guess, sure?",
                "Ask in pig latin.",
                "Type the question backwards and ask again.",
                "No way lol.",
                "Not a chance.",
                "Why?",
                "The way you smell tells me no.",
                #one whole entry:
                ("You know sometimes I have the same question, " +
                    "but then I forget what I was doing and smash my head on the ground. \n" +
                    "Because a tentacle jesus lady told me to." +
                    "\n Do you know how much that hurts? \n It doesn't. \n It's awesome."),
                "I'm not going to answer that."
            ]
            reply = random.choice(ballreplies)
            if reply == "I'm not going to answer that.":
                questionBlacklist.append(message.content)

            if message.content in questionBlacklist:
                reply = "I'm not going to answer that."
            await  client.send_message(message.channel, reply)

        if message.content.startswith('!help'):
                await  client.send_message(message.channel, 'No fuck off')

        if message.content.startswith('!insult'):
            random.seed()
            base = random.choice(insultDict['base'])
            print('insulting', message.author.name)
            while(base.find('NOUN') != -1
                    or base.find('GERUND') != -1
                    or base.find('CHAMPION') != -1
                    or base.find('BODYPART') != -1
                    or base.find('ITEM') != -1):
                # Some items can replace themselves with a different keyword, but shouldn't be able to infinitely loop.
                random.seed()
                base = base.replace('NOUN', random.choice(insultDict['noun']), 1)
                base = base.replace('GERUND', random.choice(insultDict['gerund']), 1)
                base = base.replace('CHAMPION', random.choice(insultDict['champion']), 1)
                base = base.replace('BODYPART', random.choice(insultDict['bodypart']), 1)
                base = base.replace('ITEM', random.choice(insultDict['item']), 1)
            # And release to the world:
            await client.send_message(message.channel, base)
            
        if message.content.startswith('!github'):
            await client.send_message(message.channel, 'Github Link: \n https://github.com/Scew5145/TentacleBot')

        if message.content.startswith('!quickTest'):
            # This is just for testing helper functions. Change as needed.
            await client.send_message(message.channel, pull_sum_ID('IgnusTeras'))
        if message.content.startswith('!hasfed'):
            args = message.content.split(' ')
            username = ''
            server = ''
            if len(args) == 3:
                username = args[1]
                server = args[2]
            elif len(args) == 2:
                username = args[1]
            else:
                await client.send_message(message.channel, 'Wrong Number of Arguments.' +
                '\n !hasfed [username] [server] \n or \n !hasfed [username] \n No server defaults to NA1.')
                return
            id = -1
            outputstring = ''
            if server == '':
                server = 'NA1'

            id = pull_sum_ID(username, server)
            if id == -1:
                await client.send_message(message.channel, 'Issue pulling ID from server. Check username and server ID.')
                return
            else:
                outputstring = has_fed(id[0],server)
            outputstring = outputstring.replace('USER', username)

            await client.send_message(message.channel, outputstring)

client.run(discToken)