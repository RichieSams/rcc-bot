import discord
from discord.ext import commands

import pytz
from pytz import timezone
import pytz.exceptions

from datetime import datetime
import json
import re
import os.path
import aiofiles


datetimeFormat = '%I:%M %p'

client = discord.Client()

# Load previously registered users
registeredUsers = {}

if os.path.isfile('/db/registered_users_db.json'):
    with open('/db/registered_users_db.json', 'r') as data_file:
        jsonData = json.load(data_file)
        registeredUsers = {userId: (userData[0], timezone(userData[1])) for userId, userData in jsonData.items()}


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


async def registerCommand(message):
    exploded = message.content.split(' ')

    if len(exploded) <= 1:
        await client.send_message(message.channel,
                                  'The register command syntax is:\n```\n!register <timezone> [username]\n```')
        return

    timezoneStr = exploded[1]
    user = message.author
    if len(exploded) >= 3:
        # If the user has a nickname, the format will be <@!1234...>
        # If they *don't* have a nickname, the format will be <@1234...>
        # So we try for both
        result = re.search('<@([0-9]+)>', exploded[2])
        if result and result.group(1):
            userId = result.group(1)
        else:
            result = re.search('<@!([0-9]+)>', exploded[2])
            if result and result.group(1):
                userId = result.group(1)
            else:
                await client.send_message(message.channel,
                                          "Failed to parse the member name [{0}]".format(exploded[2]))
                return

        user = next((mention for mention in message.mentions if mention.id == userId), [None])
        if user is None:
            await client.send_message(message.channel, "Failed to parse the member class for <@{0}>".format(userId))
            return

    userTZ = None
    try:
        userTZ = timezone(timezoneStr)
    except pytz.exceptions.UnknownTimeZoneError:
        await client.send_message(message.channel,
                                  "[{0}] is an unknown Timezone.\nConsult https://en.wikipedia.org/wiki/List_of_tz_database_time_zones for valid TZ names.".format(
                                      timezoneStr))
        return
    except pytz.exceptions.AmbiguousTimeError:
        await client.send_message(message.channel,
                                  "[{0}] is an ambiguous Timezone.\nConsult https://en.wikipedia.org/wiki/List_of_tz_database_time_zones for valid TZ names.".format(
                                      timezoneStr))
        return

    registeredUsers[user.id] = (user.display_name, userTZ)

    # Save the new registered users
    jsonDict = {userId: (userData[0], str(userData[1])) for userId, userData in registeredUsers.items()}
    jsonStr = json.dumps(jsonDict)

    async with aiofiles.open('/db/registered_users_db.json', mode='w') as file:
        await file.write(jsonStr)

    await client.send_message(message.channel, "Successfully registered!")


async def timeCommand(message):
    # Check if anyone is registered
    if len(registeredUsers) == 0:
        await client.send_message(message.channel, "No registered users!")
        return

    currentTime = datetime.utcnow()
    currentTime = currentTime.replace(tzinfo=pytz.utc)

    exploded = message.content.split(' ')
    if len(exploded) == 1:
        # Print everyone
        reply = "```\n"
        maxLength = 0
        for _, userInfo in registeredUsers.items():
            maxLength = max(maxLength, len(userInfo[0]))

        for _, userInfo in registeredUsers.items():
            reply += "{0}: ".format(userInfo[0])
            for __ in range(maxLength - len(userInfo[0])):
                reply += " "

            reply += "{0}\n".format(currentTime.astimezone(userInfo[1]).strftime(datetimeFormat))

        reply += "```"
        await client.send_message(message.channel, reply)
    else:
        # Try to parse the username
        userId = None
        result = re.search('<@([0-9]+)>', exploded[1])
        if result and result.group(1):
            userId = result.group(1)
        else:
            await client.send_message(message.channel,
                                      'The register command syntax is:\n```\n!time [username]\n```')
            return

        user = next((mention for mention in message.mentions if mention.id == userId), [None])
        if user is None:
            await client.send_message(message.channel, "Failed to parse the member class for <@{0}>".format(userId))
            return

        # Check if the user exists
        if userId not in registeredUsers:
            await client.send_message(message.channel,
                                      "'{0}' is not registered.".format(user.display_name))
            return

        userInfo = registeredUsers[userId]

        await client.send_message(message.channel,
                                  "```\n{0}: {1}\n```".format(userInfo[0],
                                                              currentTime.astimezone(userInfo[1]).strftime(datetimeFormat)))


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    print(message.content)

    if message.content.startswith('!register'):
        await registerCommand(message)
    elif message.content.startswith('!time'):
        await timeCommand(message)


client.run('MzMxNDk0ODI0NTg0ODA2NDAy.DDwZjQ.nBa4BE1ZfXblrx1RMOow1B9MKG0')
