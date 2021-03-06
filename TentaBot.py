import champData
import discord
import json
import random
import requests
import asyncio
import sys
import os
from lxml import html


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

cdb = champData.championDB(riotKey)

def random_CAP_image():
    smogresp = requests.get('http://www.smogon.com/forums/threads/cap-23-art-submissions.3613136/#post-7485706')
    if(smogresp.status_code != 200):
        return -1
    smogtree = html.fromstring(smogresp.content)
    imgElements = smogtree.xpath("//li[@id = 'post-7485706']/div[@class = 'messageInfo primaryContent']"
                            + "/div/article/blockquote"
                            + "/div[@class = 'bbCodeBlock bbCodeQuote bbmHideBlock']"
                            + "/div[@class = 'quotecontent']/div/blockquote/img")
    # print(lielms)
    # imgArr = lielms[0].find("//img")
    random.seed(None)
    return random.choice(imgElements).attrib['src']

def pull_champion_image(id, server = 'NA1'):
    if server.upper() in ['EUN', 'EUW', 'TR', 'BR', 'OC', 'NA', 'JP']:
        server += '1'
    elif server.upper() in ['EUNE', 'EUNE1']:
        server = 'EUN1'
    if server.upper() not in regions:
        print('bad region. Please provide valid region id.')
        return -1
    url = 'https://'
    url += server
    url += '.api.riotgames.com/lol/static-data/v3/champions/'
    url += str(id)
    url += '?champData=image&api_key='
    url += riotKey
    response = requests.get(url)
    if response.status_code != 200:
        print('something went wrong with the request. \n Status Code:', response.status_code)
        return -1
    champDict = json.loads(response.text)
    return champDict

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
    # Total riotAPI Requests inside code: 3; 2 counted towards rate limit, as one is grabbing static data
    if server.upper() in ['EUN', 'EUW', 'TR', 'BR', 'OC', 'NA', 'JP']:
        server += '1'
    elif server.upper() in ['EUNE', 'EUNE1']:
        server = 'EUN1'
    if server.upper() not in regions:
        print('bad region' + server + '. Please provide valid region id.')
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
    url += '&forAccountId='
    url += str(acc_id)
    response = requests.get(url)
    if response.status_code != 200:
        print('something went wrong with the request. \n Status Code:', response.status_code)
        return "Something is broken loading the most recent game and I don't know what: " + response.status_code
    gameDict = json.loads(response.text)

    parid = -1
    for entry in gameDict['participantIdentities']:
        print(entry)
        if 'player' in entry:
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
                'role': participant['timeline']['role'] ,
                'championId': participant['championId'],
                'matchId': most_recent_match_id,
                'largestMultiKill': participant['stats']['largestMultiKill']
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

    return playerdata, enemydata



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

        # COMMAND: !ping
        if message.content.startswith('!ping'): #Repeats what the user says
                await client.send_message(message.channel, message.content)

        # COMMAND: !8ball
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

        # COMMAND: !help
        if message.content.startswith('!help'):
                await  client.send_message(message.channel, 'No fuck off')

        # COMMAND: !insult
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

        # COMMAND: !quickTest
        # TODO: Change as nessecary for testing
        if message.content.startswith('!quickTest'):
            args = message.content.split(' ')
            id = cdb.get_champId(args[1])
            dict = cdb.get_bstats(id)
            await client.send_message(message.channel, str(dict))

        # COMMAND: !championstats | !cstats
        if message.content.startswith('!championstats') or message.content.startswith('!cstats'):
            args = message.content.split(' ')
            if len(args) != 2:
                await client.send_message(message.channel, '!championstats [champion name]')
                return

            champId = cdb.get_champId(args[1])
            statDict = cdb.get_bstats(champId)
            champimage = pull_champion_image(champId)
            if champimage == -1:
                await client.send_message(message.channel, 'Issue pulling champ image. Too many requests to API?')
                return
            champimgurl = 'http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/' + champimage['image']['full']
            em = discord.Embed(color=0x3333AA, description='**Level 1 | Growth Stat**')
            em.set_author(name=statDict['name'],icon_url=champimgurl)
            em.add_field(name='Attack Damage', value= str(statDict['stats']['attackdamage'])
                                                      + ' | '
                                                      + str(statDict['stats']['attackdamageperlevel']) )
            em.add_field(name='Attack Speed', value= str(round(0.625/(1+statDict['stats']['attackspeedoffset']),2))
                                                      + ' | '
                                                      + str(statDict['stats']['attackspeedperlevel']) )
            em.add_field(name='Mana', value=str(statDict['stats']['mp'])
                                                    + ' | '
                                                    + str(statDict['stats']['mpperlevel']))
            em.add_field(name='Health', value= str(statDict['stats']['hp'])
                                                      + ' | '
                                                      + str(statDict['stats']['hpperlevel']) )
            em.add_field(name='Armor', value= str(statDict['stats']['armor'])
                                                      + ' | '
                                                      + str(statDict['stats']['armorperlevel']) )
            em.add_field(name='Magic Resist', value= str(statDict['stats']['spellblock'])
                                                      + ' | '
                                                      + str(statDict['stats']['spellblockperlevel']) )
            await client.send_message(message.channel, embed=em)
            return



        # COMMAND: !hasfed
        # TODO: Add mobile support since apparently embeds suck ass there
        if message.content.startswith('!hasfed'):
            args = message.content.split(' ')
            server = ''
            if len(args) == 2:
                username = args[1]
            elif len(args) >= 3:
                if args[-2][-1] == ',': # The last character of the second to last argument
                    server = args[-1]
                    username = ' '.join(args[1:-1])[:-1] # Python list syntax is magic. If you can't tell, last [:-1]
                    # is for cutting off the comma at the end of the argument

                elif ',' in args[-1]: # the 'I forgot a space' case
                    temp = args[-1].split(',')
                    server = temp[-1]
                    username = args[1:-1]+temp[:-1]
                else:
                    username = ' '.join(args[1:])
            else:
                await client.send_message(message.channel, 'Wrong Number of Arguments.' + 
                                          '\n !hasfed [username], [server] \n ' +
                                          'or \n !hasfed [username] \n No server defaults to NA1.')
                return
            if server == '':
                server = 'NA1'

            id = pull_sum_ID(username, server)
            if id == -1:
                await client.send_message(message.channel, 'Issue pulling ID from server. Check username and server ID.'
                                                           +'\n Also could be an issue with the server down.')
                return
            else:
                playerdata, enemydata = has_fed(id[0],server)

            # URLs
            match_history_url = 'http://matchhistory.na.leagueoflegends.com/en/#match-details/'
            match_history_url += server
            match_history_url += '/' + str(playerdata['matchId'])
            match_history_url += '/' + str(id[0]) + '?tab=overview'

            opggurl = 'https://'
            if server[-1] == '1' or server[-1] == '2':
                server = server[:-1]
            opggurl += server
            opggurl += '.op.gg/summoner/userName='
            uname = username.replace(' ', '+')
            uname = uname.replace('_', '+')
            opggurl += uname
            
            em = discord.Embed(title= 'Feeder Report', colour=0x555555, description='[Match History]('
                                                                                       +match_history_url
                                                                                       +') | [OP.GG Profile]('
                                                                                       + opggurl + ')')

            champimage = pull_champion_image(playerdata['championId'])

            if champimage == -1:
                await client.send_message(message.channel, 'Issue pulling champ image. Too many requests to API?')
                return

            champimgurl = 'http://ddragon.leagueoflegends.com/cdn/6.2.1/img/champion/' + champimage['image']['full']

            em.set_author(name=username + ' playing ' + champimage['name'], icon_url= champimgurl)
            if playerdata['lane'] == 'BOTTOM':
                if playerdata['role'] == 'DUO_SUPPORT':
                    lane = 'Support'
                else:
                    lane = 'Bot'
            elif playerdata['lane'] == 'MID' or playerdata['lane'] == 'MIDDLE':
                lane = 'Mid'
            elif playerdata['lane'] == 'TOP':
                lane = 'Top'
            elif playerdata['lane'] == 'JUNGLE':
                lane = 'Jungle'
            else:
                lane = 'BROKEN'

            em.add_field(name='Lane', value=lane)
            KDAstring = str(playerdata['kills']) + ' / ' + str(playerdata['deaths']) + ' / ' + str(playerdata['assists'])
            enemyKDAstring = str(enemydata['kills']) + ' / ' + str(enemydata['deaths']) + ' / ' + str(enemydata['assists'])
            if playerdata['deaths'] != 0:
                kda = str(round((playerdata['kills'] + playerdata['assists']) / playerdata['deaths'], 2))
            else:
                kda = 'Perfect'
            if enemydata['deaths'] != 0:
                enemykda = str(round((enemydata['kills'] + enemydata['assists']) / enemydata['deaths'], 2))
            else:
                enemykda = 'Perfect'
            em.add_field(name='KDA', value=(kda + ' | **' + KDAstring + '**'))
            em.add_field(name="Enemy Laner's KDA", value=enemykda + ' | **' + enemyKDAstring + '**')
            em.add_field(name='CSD @ 10', value=str(round(playerdata['csdelta']['0-10'],2)))
            em.add_field(name='Gold Difference @ 10', value=str(round(playerdata['golddelta']['0-10'],2)))
            em.add_field(name='XP Difference @ 10', value=str(round(playerdata['xpdelta']['0-10'],2)))
            largestMulti = 'Zero'
            if playerdata['largestMultiKill'] == 1:
                largestMulti = 'One'
            elif playerdata['largestMultiKill'] == 2:
                largestMulti = 'Double Kill'
            elif playerdata['largestMultiKill'] == 3:
                largestMulti = 'Triple Kill'
            elif playerdata['largestMultiKill'] == 4:
                largestMulti = 'Quadra Kill'
            elif playerdata['largestMultiKill'] == 5:
                largestMulti = ':regional_indicator_p:enta Kill '
            em.add_field(name='Largest Multikill', value=largestMulti)
            em.add_field(name='Win', value=str(playerdata['win']))
            if enemykda > kda or round(playerdata['csdelta']['0-10'], 2) < 0.0 or round(playerdata['golddelta']['0-10'], 2) < 0.0:
                em.add_field(name='Feeder Status', value='True')
            else:
                em.add_field(name='Feeder Status', value='False')
            if args[0] == '!hasfedphone':
                phonem = discord.Embed(title='OP.GG Link', url=opggurl, description='Click to make the thing do the thing')
                await client.send_message(message.channel, embed=phonem)
            else:
                await client.send_message(message.channel, embed=em)

            return
        if message.content.startswith('!capart'):
            messagearr = ['first time posting [b]e gentle',
                          '(b)etter watch out for my fire drawings',
                          'my (b)est attempt at drawing shit',
                          'drawings coming right up',
                          '*vomits art*',
                          '*explodes creatively*',
                          'this took me 3 seconds to draw',
                          'help',
                          'I forgot to draw pants ;)',
                          'Photographic evidience of the holocaust [colorized]',
                          'I drew this - not some random person on the internet.',
                          'somebody pay me',
                          'ART'
                         ]
            random.seed(None)
            imgURL = random_CAP_image()
            if imgURL == -1:
                await client.send_message(message.channel, "CAP things broken")
            else:
                textoutput = random.choice(messagearr) + '\n' + imgURL
                await client.send_message(message.channel, textoutput)


client.run(discToken)