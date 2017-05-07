import discord
import json
import random
import asyncio
import sys

if len(sys.argv) != 2:
    print('add token arg only')
    exit()
token = sys.argv[1]
client = discord.Client()
random.seed(None)
with open('insults.json') as insultfile:
    insultDict = json.load(insultfile)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if message.author != client.user:
        if message.content.startswith('!ping'): #Repeats what the user says
                await client.send_message(message.channel, message.content)
        if message.content.startswith('!insult') :

            random.seed()
            base = random.choice(insultDict['base'])
            print(base)
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

client.run(token)