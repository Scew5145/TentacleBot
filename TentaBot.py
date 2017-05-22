import discord
import json
import random
import requests
import asyncio
import sys


regions = ['NA1', 'RU', 'KR', 'EUN1', 'EUW1', 'TR1', 'LA1', 'LA2', 'BR1', 'OC1', 'JP1']
if len(sys.argv) != 3:
    print('usage: TentaBot.py [discord bot key] [riot api key]')
    exit()
discToken = sys.argv[1]
riotKey = sys.argv[2]
client = discord.Client()
random.seed(None)
with open('insults.json') as insultfile:
    insultDict = json.load(insultfile)


def pull_acc_ID(username, server = 'NA1'):
    # Uses the Riot API to grab the account's ID and return it. Doesn't return region, as it's an input.
    if server.upper() in ['EUN', 'EUW', 'TR', 'BR', 'OC', 'NA', 'JP']:
        server += '1'
    elif server.upper() in ['EUNE', 'EUNE1']:
        server = 'EUN1'
    if server.upper() not in regions:
        print('bad region. Please provide valid region id.')
        return -1
    url = 'https: // ' \
          + server \
          +'.api.riotgames.com / lol / summoner / v3 / summoners / by - name / '\
          + username \
          + '?api_key =' \
          + riotKey
    response = requests.get(url)
    if( response.status_code != 200):
        print('something went wrong with the request. \n Status Code:', response.status_code)
        return -1
    accID = response.content['accountId']
    return accID

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

            if(message.content in questionBlacklist):
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

client.run(discToken)