#TemporalMonkey, created by Airtoum

from typing import Any, Coroutine
import discord
from discord import user
from discord.ext import commands
from discord.ext.commands import Bot
from discord.interactions import Interaction
from discord.utils import get
import random
import asyncio
import time
import pickle
import json
import os
import WackyCodex.WackyCodex as WackyCodex
from WackyCodex.WackyCodex import Ctx
from WackyCodex.WackyCodex import finish, send_and_finish
import WackyCodex.WackyCodexDisplayer as WackyCodexDisplayer
import re
import math

intents = discord.Intents.default()
intents.guild_messages = True
intents.dm_messages = True
intents.message_content = True
intents.guilds = True
#intents.message_contents = True
bot = commands.Bot(command_prefix='m^', intents=intents)
intents.members = True
client = discord.Client(intents=intents)
prefix = '^'
num_self_responses = 0

#wacky_codex_world = Ctx()

with open('config.json', 'r') as thefile:
    config = json.load(thefile)

with open('corncob_lowercase.txt','r') as myfile:
    AllWords = myfile.read().split("\n")
    

# Simple Abstract Functions

def printlist(list):
    print("PRINTING LIST")
    for x in list:
        print("\t" + x)

def is_str_int(n):
    try:
        int(n)
        return True
    except ValueError:
        return False

# General Functions Specific to This Program

def parsecommand(string):
    inquotes = False
    escape = False
    special = False
    charlist = list(string)
    args = [""]
    for c in charlist:
        special = False
        if escape:
            args[-1] += c
            escape = False
        else:
            if c == " " and not inquotes:
                args.append("")
                special = True
            if c == "\n" and not inquotes:
                args.append("")
                special = True
            if c == "\t" and not inquotes:
                args.append("")
                special = True
            if c == "\"":
                inquotes = not inquotes
                special = True
            if c == "“":
                inquotes = not inquotes
                special = True
            if c == "”":
                inquotes = not inquotes
                special = True
            if c == "\\":
                escape = True
                special = True
            if not special:
                args[-1] += c
    return args

def parseuser(string, channel: discord.CategoryChannel) -> discord.User | None:
    target = None
    for u in channel.guild.members:
        if u.name == string or u.display_name == string or (is_str_int(string) and u.id == int(string)):
            target = u
            print("FOUND USER: " + u.name + ", " + u.display_name + ", " + str(u.id))
            break
    return target

def find_guild(server_name: str) -> discord.Guild:
    for guild in client.guilds:
        if guild.name == server_name:
            return guild
    raise ValueError


# this system isn't very scalable. If this ever becomes an issue, either 
#  ditch the human-readability with something like SQLite 
#  or split the users across files in a subfolder.

def load_all_users() -> dict:
    try:
        with open('AllMonkeyUsers.json', 'r') as thefile:
            x = json.load(thefile)
            return x
    except FileNotFoundError:
        return {}

def get_user(user_id) -> dict:
    x = load_all_users().setdefault(str(user_id), {})
    return x

def save_to_all_users(data):
    with open("AllMonkeyUsers.json", "w") as thefile:
        json.dump(data, thefile, indent=4)

def save_user(user_id, monkey_user):
    all_users = load_all_users()
    all_users[str(user_id)] = monkey_user
    save_to_all_users(all_users)

async def multisend(channel, message, enclose=''):
    cursor = 0
    while len(message) > cursor:
        await channel.send(enclose + message[cursor: cursor + 2000 - 2 * len(enclose)] + enclose)
        cursor += 2000 - 2 * len(enclose)

async def auth_check_dev_command(channel, author):
    if author.id in [152885068606603265]:
        return False
    await channel.send(f'You do not have permission to use this command.')
    return True

async def send_maybe_empty(channel, message):
    if message:
        await channel.send(message)
        return
    await channel.send('_ _')

async def send_multiple_messages(channel, messages):
    if (sum(len(message) for message in messages) + (len('\n') * len(messages) - 1)) > 2000:
        for message in messages:
            await multisend(channel, message)
    else:
        await channel.send('\n'.join(messages))


all_server_dm_data: dict[str, 'ServerDMData']
all_wacky_contexts: dict[str, WackyCodex.Ctx]
NULL_WACKY_CODEX = WackyCodex.Ctx
NULL_WACKY_CODEX.ctx_created_from = '(missing or deleted world)'


# Classes

class ServerDMData:
    def __init__(self):
        self.availible_wacky_contexts: list[str] = []
        self.current_wacky_context_name: str|None = None

    async def get_wacky_context_or_return_message(self, channel) -> str | None:
        if self.current_wacky_context_name:
            return self.current_wacky_context_name
        await channel.send(f'This Server/DM channel does not have a Wacky Codex world yet! Create one with `{prefix}wc-new-world`, or switch to one with `{prefix}wc-switch-world`.')
        return None
    
    @staticmethod
    def create_identifier_from_channel(channel: discord.TextChannel) -> str:
        if isinstance(channel, discord.DMChannel):
            return f'DM:{channel.id}'
        if isinstance(channel, discord.TextChannel):
            return f'Server:{channel.guild.id}'
        
    @staticmethod
    def create_identifier_from_server(server: discord.Guild) -> str:
        return f'Server:{server.id}'
    
    @staticmethod
    async def create_identifier_from_user(user: discord.User | discord.Member) -> str:
        if user.dm_channel:
            return f'DM:{user.dm_channel.id}'
        else:
            return f'DM:{(await user.create_dm()).id}'

class Monkey:       # this class contains everything and gets saved after every command.
                    # this class does not contain large external files that would be unneccessary to load each time. 
                    # does not incorporate permanent storage.   

    def __init__(self):
        self.selfinfluence = False
        self.telephonechannel = None
        self.connected_channel = None


class Commands:
    null_short_desc = "This command does nothing."
    async def null(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        await channel.send("Whoops! That command hasn't been setup yet.")

    hello_short_desc = "Hello!"
    async def hello(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        await channel.send("Hello!")

    goodbye_short_desc = "Goodbye!"
    async def goodbye(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        await channel.send("Goodbye!")

    repeatme_args = "<message>"
    repeatme_short_desc = "Repeats you."
    async def repeatme(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        await channel.send(" ".join(args))

    clearreactions_args = "<message id>"
    clearreactions_short_desct = "Removes all reactions on a message."
    async def clearreactions(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        # usage: ^clearreactions id
        if is_str_int(args[0]):
            try:
                #newchannel = client.get_channel(int(args[1]))
                message = await channel.fetch_message(int(args[0]))
                await message.clear_reactions()
            except discord.NotFound:
                await channel.send("Error 404: Not found. Message " + args[0] + " cannot be found.")
            except discord.Forbidden:
                await channel.send("Error 403: Foribidden. Message " + args[0] + " cannot be accessed, or I have insufficient permissions to clear the reactions.")
            except discord.HTTPException as err:
                msg = "Oh dear. This is an HTTP Exception. Here are the details:\n"
                msg += "response: " + str(err.response) + "\n"
                msg += "text: " + err.text + "\n"
                msg += "status: " + str(err.status) + "\n"
                msg += "code: " + str(err.code)
                await channel.send(msg)
        else:
            await channel.send("\"" + args[0] + "\" is not a valid numerical message ID.")

    setchannel_args = "<channel ID>"
    setchannel_short_desc = f"Sets up which channel will be used for {prefix}telephone. You may have to turn on developer mode to get the channel ID."
    async def setchannel(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        if is_str_int(args[0]): 
            monkey.telephonechannel = int(args[0])
            await channel.send("Channel set to " + args[0])
        else:
            await channel.send("That's not a valid numerical channel ID.")
    
    telephone_args = "<message>"
    telephone_short_desc = f"Relays a message in another channel. Use {prefix}setchannel to select a channel."
    async def telephone(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        if monkey.telephonechannel == None:
            await channel.send("No channel has been set! Use `^setchannel <channel ID>` to set the channel.")
        else:
            targetchannel = client.get_channel(monkey.telephonechannel)
            if targetchannel == None:
                await channel.send("I can't find channel " + str(monkey.telephonechannel) + "!")
            else:
                await targetchannel.send(" ".join(args))

    debug_short_desc = "Prints out debug information."
    async def debug(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        print("THE DEBUG COMMAND!")
        msg = 'A\tB\tC\nAy\tBe\tCa\nAna\tBeta\tCera\n'
        await channel.send(msg)

    setmystring_args = "<message>"
    setmystring_short_desc = "Sets your personalized string to whatever text you want. Can be viewed with " + prefix + "mystring."
    async def setmystring(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            with open('personalizedstrings.monkey', 'rb') as thefile:
                allstrings = pickle.load(thefile)
        except FileNotFoundError:
            allstrings = {}
        allstrings[author.id] = " ".join(args)
        with open("personalizedstrings.monkey", "wb") as thefile:
            pickle.dump(allstrings,thefile)

    mystring_args = "[user]"
    mystring_short_desc = "Displays what a user has set their personalized string to be, or your own string if unspecified."
    async def mystring(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            with open('personalizedstrings.monkey', 'rb') as thefile:
                allstrings = pickle.load(thefile)
        except FileNotFoundError:
            allstrings = {}
        if len(args) == 0:
            target = author
        else:
            target = parseuser(args[0], channel)
            if target == None:
                await channel.send("Unable to locate that user.")
                return
        if target.id in allstrings:
            await channel.send(allstrings[target.id])
        else:
            await channel.send("The desired user hasn't assigned themself a string yet.")

    honk_short_desc = "Plays a loud sound in the VC."
    async def honk(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        vc = await client.get_channel(743322729176105060).connect()
        vc.play(discord.FFmpegPCMAudio(executable="C:/Program Files/ffmpeg/bin/ffmpeg.exe", source="C:/Users/aidan/Documents/TemporalMonkey/TemporalMonkey v2/horn2.mp3"))
        while (vc.is_playing()):
            time.sleep(1)
        time.sleep(2)
        await vc.disconnect()

    scaleofgay_short_desc = "Tells you where you rank on the scale of gay."
    async def scaleofgay(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        if len(args) > 0 and args[0] == "Dimetrio":
            await channel.send(prefix + "playfile C:\\\\Users\\\\aidan\\\\Downloads\\\\DimetrioTime (1).wav")
            return
        the_user = get_user(author.id)
        scale_of_gay = the_user.setdefault("scaleofgay", random.randint(0, 10))
        save_user(author.id, the_user)
        await channel.send(f"You have a {scale_of_gay} on the scale of gay")

    randomsong_short_desc = "Plays a random song from a list of music Airtoum has bought."
    async def randomsong(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        song_list = [
            "C:/Users/aidan/Music/nanobii - Children of the Sky.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Brave Adventures/Linus from the Stars - Brave Adventures - 01 Clouds Beneath Our Feet.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Brave Adventures/Linus from the Stars - Brave Adventures - 02 Shipwrecked on the Moon.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Brave Adventures/Linus from the Stars - Brave Adventures - 03 On My Way.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Hopeless Dreamer/Linus from the Stars - Hopeless Dreamer - 01 Evangeline.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Hopeless Dreamer/Linus from the Stars - Hopeless Dreamer - 02 Glass Beads.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Hopeless Dreamer/Linus from the Stars - Hopeless Dreamer - 03 Dear Sorrow.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Hopeless Dreamer/Linus from the Stars - Hopeless Dreamer - 04 It's Alright, It's Okay.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Hopeless Dreamer/Linus from the Stars - Hopeless Dreamer - 05 (The Jungle Is) Wild & Free.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Lovely- Wonderful Thoughts/Linus from the Stars - Lovely, Wonderful Thoughts - 01 Starry Eyed",
            "C:/Users/aidan/Music/Linus from the Stars - Lovely- Wonderful Thoughts/Linus from the Stars - Lovely, Wonderful Thoughts - 02 Dream Theatre.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Lovely- Wonderful Thoughts/Linus from the Stars - Lovely, Wonderful Thoughts - 03 Under the Weather.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Lovely- Wonderful Thoughts/Linus from the Stars - Lovely, Wonderful Thoughts - 04 Tokyo.mp3",
            "C:/Users/aidan/Music/Linus from the Stars - Lovely- Wonderful Thoughts/Linus from the Stars - Lovely, Wonderful Thoughts - 05 Autumn Leaves.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 01 Hidden Path.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 02 Daybreaker.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 03 Body Jammer.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 04 Atom Sampler.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 05 Escalade.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 06 Stride.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 07 Coast.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 08 Panic Beach.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 09 Precarious.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 10 Progress.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 11 Machine Politics.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 12 NightSquad Redux.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 13 Give Me a Break.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 14 Nightlife.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 15 Race Around the Desert.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 16 Keep Going.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 17 Grid Voyage.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 18 Octagon Force.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 19 Viscid.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 20 Skelter.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 21 Supra Zone.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 22 Feelin' Better.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 23 Boundless.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 24 Floating.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 25 Sky Maneuvers.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 26 Frenetic.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 27 Race Around the Galaxy.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 28 Jumper 2.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 29 Hidden path (Rapid Route Mix).mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 30 Big Bad Break.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 31 The Chase.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 32 Dance-Off.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 33 Flukt.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 34 Market District.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 35 Everyday Heroes.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 36 Starfall.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 37 Starcrater.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 38 Dreamscape.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 39 Felicity.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 40 Thunderzone 2.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 41 Slink.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 42 Doomsday.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 43 Running From Demons.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 44 Pain Engine.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 45 Wormloader.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 46 Brain Damage.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 47 Duskbreaker.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 48 Gabberfly.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 49 Deluding Beats.mp3",
            "C:/Users/aidan/Music/Waterflame - Vast/Waterflame - Vast - 50 Astral Space.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 01 Go For Distance.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 02 Relapse.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 03 No Party Like a Mojang Party.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 04 A Rose in a Field.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 05 Sevcon.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 06 Chip Zeal.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 07 Houston.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 08 Gront is a Muppet.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 09 Interlude.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 10 The Trials of MAN.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 11 Snowcones.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 12 Viceroy Danny Von B.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 13 Artifact Hunter.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 14 VIRTuoso Sexy.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 15 Vindicate Me (instrumental).mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 16 Wintory Fresh.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 17 Biceps Blaster.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 18 Micksplosions.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 19 Peanut Butter Cupquakes.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 20 The Glory Days.mp3",
            "C:/Users/aidan/Music/Big Giant Circles - The Glory Days/Big Giant Circles - The Glory Days - 21 The Chiptune Legacy.mp3"
        ]
        print("randomsong command")
        try:
            vc = await client.get_channel(743322729176105060).connect(timeout=15)
        except discord.ClientException:
            vc = client.voice_clients[0]
            vc.stop()
        except TimeoutError:
            await channel.send("I failed to connect to voice! <:(")
            return
        print(vc)
        vc.play(discord.FFmpegPCMAudio(executable="C:/Program Files/ffmpeg/bin/ffmpeg.exe", source=random.choice(song_list)))
        print("I should be playing the song now")

    playfile_args = "<path>"
    playfile_short_desc = "Plays in the VC a file at the designated path on the machine TemporalMonkey is running on."
    async def playfile(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            vc = await client.get_channel(743322729176105060).connect()
        except discord.ClientException:
            vc = client.voice_clients[0]
            vc.stop()
        vc.play(discord.FFmpegPCMAudio(executable="C:/Program Files/ffmpeg/bin/ffmpeg.exe", source=" ".join(args)))
    
    stop_short_desc = "Makes TemporalMonkey leave the voice channel."
    async def stop(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        if client.voice_clients:
            client.voice_clients[0].stop()
            await client.voice_clients[0].disconnect()

    randomword_short_desc = "Prints a random English word."
    async def randomword(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        await channel.send(random.choice(AllWords))

    help_args = "[command name]"
    help_short_desc = "Lists all commands, or gives a detailed explanation of a single command if given an argument"
    async def help(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        if len(args) > 0:
            lookupcommand = commandlist[0]
            commands = commandlist[1]
            key = prefix + args[0].replace(prefix,"")
            helpcommand = lookupcommand[key]
            if not key in lookupcommand:
                await channel.send("That is not a command.")
                return
            msg = "﻿"
            command_args = getattr(commands, f"{helpcommand.__name__}_args", "")
            if len(command_args) > 0:
                command_args = " " + command_args
            description = getattr(commands, f"{helpcommand.__name__}_short_desc", "")
            if len(description) > 0:
                msg += f"{key}{command_args}: {description} \n\n"
            else:
                msg += f"{key}{command_args}\n\n"
            await channel.send(msg)
        else:    
            msg = ""
            lookupcommand = commandlist[0]
            commands = commandlist[1]
            for key, value in lookupcommand.items():
                command_args = getattr(commands, f"{value.__name__}_args", "")
                if len(command_args) > 0:
                    command_args = " " + command_args
                description = getattr(commands, f"{value.__name__}_short_desc", "")
                if len(description) > 0:
                    msg += f"{key}{command_args}: {description} \n\n"
                else:
                    msg += f"{key}{command_args}\n\n"
            await multisend(channel, msg, "```")

    sendfile_args = "<filepath>"
    sendfile_short_desc = "Sends a file from my computer."
    async def sendfile(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        filename = " ".join(args)
        if "config.json" in filename:
            await channel.send("That file contains sensitive data!")
            return
        with open(filename, "rb") as thefile:
            await channel.send(file=discord.File(thefile))

    ls_args = "<path>"
    ls_short_descrition = "Lists all files at this path."
    async def ls(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        await channel.send("\n".join(os.listdir(" ".join(args))))

    setkey_args = "<key> <value>"
    setkey_short_desc = "Sets a message to be associated with a key. Using ^key with the same key will display the message that you set. Keys are shared globally across all servers."
    async def setkey(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            with open('savedkeys.monkey', 'rb') as thefile:
                allkeys = pickle.load(thefile)
        except FileNotFoundError:
            allkeys = {}
        allkeys[args[0]] = " ".join(args[1:])
        with open("savedkeys.monkey", "wb") as thefile:
            pickle.dump(allkeys,thefile)

    key_args = "<key>"
    key_short_desc = "Displays a message associated with a saved key. Create keys with ^setkey <key> <value>"
    async def key(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            with open('savedkeys.monkey', 'rb') as thefile:
                allkeys = pickle.load(thefile)
        except FileNotFoundError:
            allkeys = {}
        key = args[0]
        if key in allkeys:
            await channel.send(allkeys[key])
        else:
            await channel.send("That key has not been given a value.")

    convertkeys_short_desc = "This command converts the saved keys from the old format to the new one. This command should never be run more than once."
    async def convertkeys(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        with open('keystrings.txt', 'r') as myfile:
            txt = myfile.read()
            if (txt.endswith("\n")):
                txt = txt [:-1]
            personalizedStringsArray = txt.split('‡')
            personalizedStringsGrid = []
            for x in personalizedStringsArray:
                personalizedStringsGrid.append(x.split('‰'))
            keyStrings = {}
            for x in personalizedStringsGrid:
                keyStrings[x[0]] = x[1]
            with open("savedkeys.monkey", "wb") as thefile:
                pickle.dump(keyStrings,thefile)

    randomkey_short_desc = "Selects a random key and displays its associated message."
    async def randomkey(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            with open('savedkeys.monkey', 'rb') as thefile:
                allkeys = pickle.load(thefile)
        except FileNotFoundError:
            allkeys = {}
        key = random.choice(list(allkeys.keys()))
        await channel.send(prefix + "key " + key)

    doublekey_args = "<key> <key>"
    doublekey_short_desc = "Displays the messages of TWO keys! (be careful with this one)"
    async def doublekey(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        if len(args) != 2:
            await channel.send("Give two arguments: two keys to access")
        try:
            with open('savedkeys.monkey', 'rb') as thefile:
                allkeys = pickle.load(thefile)
        except FileNotFoundError:
            allkeys = {}
        key1 = args[0]
        key2 = args[1]
        if key1 in allkeys and key2 in allkeys:
            await channel.send(allkeys[key1])
            await channel.send(allkeys[key2])
        else:
            await channel.send("One or both of those keys has/have not been given a value.")

    createdeck_args = "<deck key>"
    createdeck_short_desc = "Creates a new deck under a key. <deck key> is the name of the deck, and is used to access it. Decks contain cards, and cards can be drawn from a deck with ^drawdeck, ^draw, or ^deck to remove a card from the deck and display it. The discarded cards can be put back into the deck with the ^reshuffle command. To make a deck, use the ^setcard command. Decks can also be instead treated like dice, in which you use ^roll to get a random card in the deck (this ignores which ones are in the deck's discard pile.)"
    async def createdeck(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            with open('saveddecks.monkey', 'rb') as thefile:
                alldecks = pickle.load(thefile)
        except FileNotFoundError:
            alldecks = {}
        alldecks[args[0]] = {}
        with open("saveddecks.monkey", "wb") as thefile:
            pickle.dump(alldecks,thefile)

    setcard_args = "<deck key> <card number> <card text>"
    setcard_short_desc = "Creates or changes a card within a deck. <deck key> determines which deck you're editing, and each card in the deck must be given a different identifier using <card number>. To edit an existing card, use the same card number as it."
    async def setcard(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        index = 0
        if len(args) < 3:
            await channel.send("Requres 3 arguments: <deck key> <card number> <card text>")
            return
        if is_str_int(args[1]):
            index = int(args[1])
        else:
            await channel.send("Second argument must be a number: <deck key> <card number> <card text>")
            return
        value = " ".join(args[2:])
        try:
            with open('saveddecks.monkey', 'rb') as thefile:
                alldecks = pickle.load(thefile)
        except FileNotFoundError:
            alldecks = {}
            alldecks[args[0]] = {}
        alldecks[args[0]][index] = value
        with open("saveddecks.monkey", "wb") as thefile:
            pickle.dump(alldecks,thefile)

    removecard_args = "<deck key> <card number>"
    removecard_short_desc = "Removes a card from a deck at card slot <card number>."
    async def removecard(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        index = 0
        if len(args) < 2:
            await channel.send("Requres 2 arguments: <deck key> <card number>")
            return
        if is_str_int(args[1]):
            index = int(args[1])
        else:
            await channel.send("Second argument must be a number: <deck key> <card number>")
            return
        try:
            with open('saveddecks.monkey', 'rb') as thefile:
                alldecks = pickle.load(thefile)
        except FileNotFoundError:
            alldecks = {}
            alldecks[args[0]] = {}
        alldecks[args[0]].pop(index)
        with open("saveddecks.monkey", "wb") as thefile:
            pickle.dump(alldecks,thefile)
    
    drawdeck_args = "<deck key>"
    drawdeck_short_desc = "Draws the top card from a deck with key <deck key>. If the deck is empty, use ^reshuffle."
    async def drawdeck(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            with open('saveddecks.monkey', 'rb') as thefile:
                alldecks = pickle.load(thefile)
        except FileNotFoundError:
            alldecks = {}
        try:
            with open('saveddrawncards.monkey', 'rb') as thefile:
                alldrawncards = pickle.load(thefile)
        except FileNotFoundError:
            alldrawncards = {}
        deck = args[0]
        if not deck in alldecks:
            await channel.send("That deck has not been created.")
            return
        if len(alldecks[deck]) == 0:
            await channel.send("That deck has zero cards.")
            return
        drawn = alldrawncards.setdefault(deck, set())
        undrawn = []
        for key in alldecks[deck]:
            if not key in drawn:
                undrawn.append(key)
        if len(undrawn) == 0:
            await channel.send("That deck has run empty. Reshuffle with ^reshuffle " + deck)
            return
        index = random.choice(undrawn)
        alldrawncards[deck].add(index)
        with open("saveddrawncards.monkey", "wb") as thefile:
            pickle.dump(alldrawncards,thefile)
        await channel.send(alldecks[deck][index])

    reshuffle_args = "<deck key>"
    reshuffle_short_desc = "Reshuffles a deck, shuffling in the discard pile."
    async def reshuffle(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            with open('saveddrawncards.monkey', 'rb') as thefile:
                alldrawncards = pickle.load(thefile)
        except FileNotFoundError:
            alldrawncards = {}
        deck = args[0]
        alldrawncards[deck] = set()
        with open("saveddrawncards.monkey", "wb") as thefile:
            pickle.dump(alldrawncards,thefile)

    rolldeck_args = "<deck key>"
    rolldeck_short_desc = "Rolls a deck as if it were a die instead. All cards (discard pile and deck) are treated like die faces."
    async def rolldeck(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            with open('saveddecks.monkey', 'rb') as thefile:
                alldecks = pickle.load(thefile)
        except FileNotFoundError:
            alldecks = {}
        deck = args[0]
        if not deck in alldecks:
            await channel.send("That deck has not been created.")
            return
        if len(alldecks[deck]) == 0:
            await channel.send("That deck has zero cards.")
            return
        index = random.choice(list(alldecks[deck].keys()))
        await channel.send(alldecks[deck][index])

    listdecks_short_desc = "Lists all decks. (hmm.)"
    async def listdecks(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            with open('saveddecks.monkey', 'rb') as thefile:
                alldecks = pickle.load(thefile)
        except FileNotFoundError:
            alldecks = {}
        if len(alldecks.keys()) == 0:
            await channel.send("There are no decks.")
        await multisend(channel, "\n".join(alldecks.keys()), enclose='```')
    
    spreaddeck_short_desc = "Lists all cards in a deck."
    async def spreaddeck(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        try:
            with open('saveddecks.monkey', 'rb') as thefile:
                alldecks = pickle.load(thefile)
        except FileNotFoundError:
            alldecks = {}
        deck = args[0]
        if not deck in alldecks:
            await channel.send("That deck has not been created.")
            return
        if len(alldecks[deck]) == 0:
            await channel.send("That deck has zero cards.")
            return
        await multisend(channel, "\n".join( (f'{key}: {value}' for key, value in alldecks[deck].items()) ), enclose='```')

    flipcoin_short_desc = f"Flips a coin. 50% chance of heads, 50% chance of tails."
    async def flipcoin(self, args, author: discord.User, channel, monkey: Monkey, commandlist, extra):
        await channel.send("tails")


    async def respond_ok(self, interaction: discord.Interaction):
        await discord.InteractionResponse(interaction).send_message('ok')
        return True

    async def respond_nah(self, interaction: discord.Interaction):
        await discord.InteractionResponse(interaction).edit_message(view=None)
        if interaction.message:
            await interaction.message.add_reaction('\u274C')

    async def embed_test(self, args, author, channel, monkey, commandlist, extra):
        the_view = discord.ui.View()
        button1 = discord.ui.Button(label='GOOD', style=discord.ButtonStyle.green)
        button1.callback = self.respond_ok
        button2 = discord.ui.Button(label='BAD', style=discord.ButtonStyle.red)
        button2.callback = self.respond_nah
        the_view.add_item(button1)
        the_view.add_item(button2)
        await channel.send('nason', embed=discord.Embed.from_dict(
            {
                "id": 652627557,
                "title": "About Embed Generator",
                "description": "Embed Generator is a powerful tool that enables",
                "color": 16776960,
                "fields": [
                    {
                    "id": 311448947,
                    "name": "eggs",
                    "value": "  CREATE Goblin\n  IF MYSELF HAS Golden\n  IF MYSELF HAS Silver\n  CREATE Goblin\n  GIVE SELF Gold AND GIVE SELF Gold AND GIVE SELF Gold\\n  IF TRUE\\n  IF NOT FALSE\\n  IF NOT TRUE\\n  IF FALSE\\n  FIND Gold\\n  FIND SOMETHING\\n  FIND SOMETHING THAT HAS Wooden\\n  FIND SOMETHING THAT IS A Gold\n  FIND SOMETHING THAT IS THAT\n  FIND SOMETHING THAT IS ONE OF THESE\n  FIND NEAREST\n  FIND NEAREST THA",
                    "inline": True
                    },
                ],
                "author": {
                    "name": "e"
                }
            }),
            view=the_view)
        
    async def wacky_codex_create_player(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        player_name = author.global_name or author.name
        player_creation = None
        already_defined =  player_name in ctx.object_definitions
        if already_defined:
            embed_message = f'```OBJECT\n{ctx.object_definitions[player_name].source}```'
        else:
            player_creation = ctx.create_player(player_name, str(author.id))
            diffs, warnings = next(player_creation)
            for i, diff in enumerate(diffs):
                if diff:
                        diffs[i] = f'```diff\n{diff}```'
                else:
                    diffs[i] = f'```No change```'
            embed_message = '\n'.join(diffs)
        embed = discord.Embed(color=16776960, description=embed_message)
        the_view = discord.ui.View()
        button1 = discord.ui.Button(label='GOOD', style=discord.ButtonStyle.green)
        button2 = discord.ui.Button(label='BAD', style=discord.ButtonStyle.red)
        async def respond_ok(interaction: discord.Interaction):
            await discord.InteractionResponse(interaction).edit_message(view=None)
            if interaction.message:
                await interaction.message.add_reaction('\u2705')
            if already_defined:
                ctx.spawn(player_name, WackyCodex.Vector.zero(), False)
                await interaction.channel.send(f'Your player has been spawned, {author.global_name or author.name}!') # type: ignore
            else:
                send_and_finish(player_creation, True)   # type: ignore
                await interaction.channel.send(f'Your player has been created, {author.global_name or author.name}! Use `{prefix}wc-look`, `{prefix}wc-draw`, or `{prefix}wc-scan` to take a look around!') # type: ignore
        async def respond_nah(interaction: discord.Interaction):
            await discord.InteractionResponse(interaction).edit_message(view=None)
            if interaction.message:
                await interaction.message.add_reaction('\u274C')
            if player_creation:
                player_creation.close()
        button1.callback = respond_ok
        button2.callback = respond_nah
        the_view.add_item(button1)
        the_view.add_item(button2)
        if already_defined:
            await channel.send("There is already a character for you! Just to be sure, does this look good?", embed=embed, view=the_view)
        else:
            await channel.send("Welcome to Wacky Codex!\nLet's create a character for you... Does this look good?", embed=embed, view=the_view)

    async def wacky_codex_define(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if definition := re.findall(r'```(.+)```', extra['rawinput'], re.RegexFlag.DOTALL):
            server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
            ctx_name = await server_data.get_wacky_context_or_return_message(channel)
            if not ctx_name:
                return
            ctx = all_wacky_contexts[ctx_name]
            compilation = ctx.compile_and_prompt(definition[0])
            diffs = []
            warnings = []
            try:
                diffs, warnings = next(compilation)
            except WackyCodex.CompilationError as compilation_error:
                await channel.send(str(compilation_error))
                return
            for i, diff in enumerate(diffs):
                if diff:
                    diffs[i] = f'```diff\n{diff}```'
                else:
                    diffs[i] = f'```No change```'
            embed_description = '\n'.join(diffs)
            warnings = WackyCodex.format_counted(WackyCodex.count_and_deduplicate(warnings))
            for warning in warnings:
                embed_description += f'\n{warning}\n'
            embed = discord.Embed(color=16776960, description=embed_description)
            the_view = discord.ui.View()
            button1 = discord.ui.Button(label='GOOD', style=discord.ButtonStyle.green)
            button2 = discord.ui.Button(label='BAD', style=discord.ButtonStyle.red)
            async def respond_ok(interaction: discord.Interaction):
                await discord.InteractionResponse(interaction).edit_message(view=None)
                if interaction.message:
                    await interaction.message.add_reaction('\u2705')
                send_and_finish(compilation, True)
            async def respond_nah(interaction: discord.Interaction):
                await discord.InteractionResponse(interaction).edit_message(view=None)
                if interaction.message:
                    await interaction.message.add_reaction('\u274C')
                compilation.close()
            button1.callback = respond_ok
            button2.callback = respond_nah
            the_view.add_item(button1)
            the_view.add_item(button2)
            await channel.send("Your definition can be added to the game! Does this look good?", embed=embed, view=the_view)
        else:
            await channel.send("Invalid format. Be sure to surround your definition with \\`\\`\\` to turn it into a code block.")

    async def wacky_codex_do(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if len(args) < 1:
            return await channel.send(f'Correct syntax: {prefix}wc-do <verb> (other)')
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        verb = args[0]
        other = " ".join(args[1:]) if len(args) >= 2 else None
        try:
            owner = ctx.focus(str(author.id))
            ctx.control_owned_object(str(author.id), verb, other)
        except LookupError as err:
            extra_msg = ''
            if 'player-missing' in err.args:
                extra_msg = f'There is no object belonging to you for you to control. Maybe try {prefix}wc-start to make one?'
            return await channel.send(f'{err.args[0]}\n{extra_msg}')
        ctx.tick()
        do_message = owner.read_and_clear_output()
        objects_seen = ctx.look_around_as_owned_object(str(author.id))
        player = ctx.get_object_by_owner(str(author.id))
        look_message = WackyCodexDisplayer.display_from_preference(objects_seen, player, owner.display_mode)
        await send_multiple_messages(channel, [do_message, look_message])

    async def wacky_codex_spawn(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if len(args) < 1:
            return await channel.send(f'Correct syntax: {prefix}wc-spawn <name>')
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        name = " ".join(args)
        spawn_at_object = None
        owner = ctx.focus(str(author.id))
        try:
            spawn_at_object = ctx.get_object_by_owner(str(author.id))
        except LookupError as err:
            extra_msg = ''
            if 'player-missing' in err.args:
                extra_msg = f'There is no object belonging to you for you to control. (This command spawns something at your position.) Maybe try {prefix}wc-start to make one?'
            return await channel.send(f'{err.args[0]}\n{extra_msg}')
        ctx.spawn(name, spawn_at_object.position, output_creation=True)
        await channel.send(owner.read_and_clear_output())

    async def wacky_codex_lookup(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if len(args) < 1:
            return await channel.send(f'Correct syntax: {prefix}wc-lookup <word>')
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        word = " ".join(args)
        await multisend(channel, ctx.lookup(word))

    async def wacky_codex_spill(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if len(args) < 1:
            return await channel.send(f'Correct syntax: {prefix}wc-spill <word>')
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        word = " ".join(args)
        await multisend(channel, ctx.spill(word), '```')

    async def wacky_codex_look(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        try: 
            objects_seen = ctx.look_around_as_owned_object(str(author.id))
        except LookupError as err:
            extra_msg = ''
            if 'player-missing' in err.args:
                extra_msg = f'There is no object belonging to you for you to look around as. Maybe try {prefix}wc-start to make one?'
            return await channel.send(f'{err.args[0]}\n{extra_msg}')
        player = ctx.get_object_by_owner(str(author.id))
        ctx.clear_output()
        # description_list = [
        #     f'**{obj.definition}**<multiplicity_of_object>{
        #         '\n- '+', '.join(WackyCodex.format_counted(WackyCodex.count_and_deduplicate(obj.inventory))) if obj.inventory else ''
        #     }' for obj in objects_seen
        # ]
        # description_list = WackyCodex.format_counted_special(WackyCodex.count_and_deduplicate(description_list), '<multiplicity_of_object>')
        # message = '\n'.join(description_list)
        message = WackyCodexDisplayer.look(objects_seen, player)
        owner = ctx.focus(str(author.id))
        owner.display_mode = 'l'
        await channel.send(message)

    async def wacky_codex_draw(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        try:
            objects_seen = ctx.look_around_as_owned_object(str(author.id))
        except LookupError as err:
            extra_msg = ''
            if 'player-missing' in err.args:
                extra_msg = f'There is no object belonging to you for you to look around as. Maybe try {prefix}wc-start to make one?'
            return await channel.send(f'{err.args[0]}\n{extra_msg}')
        player = ctx.get_object_by_owner(str(author.id))
        ctx.clear_output()
        # display = []
        # empty_symbol = '. '
        # for i in range(15):
        #     display.append([])
        #     for j in range(15):
        #         display[i].append([])
        # tags = ' 23456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01'
        # symbols_used = {}
        # def find_symbol(char, objs):
        #     for tag in tags:
        #         if char + tag in symbols_used:
        #             compare_objs = symbols_used[char + tag]
        #             if WackyCodex.hash_object_list(compare_objs) == WackyCodex.hash_object_list(objs):
        #                 return char + tag
        #         else:
        #             symbols_used[char + tag] = objs
        #             return char + tag
        #     return char + '*'
        # for obj in objects_seen:
        #     delta = obj.position - player.position
        #     clamped = delta.clamped(7)
        #     if math.isnan(clamped.x) or math.isnan(clamped.y) or math.isnan(clamped.z):
        #         continue
        #     display[int(-clamped.y)+7][int(clamped.x)+7].append(obj)
        # for i, row in enumerate(display):
        #     for j, cell in enumerate(row):
        #         if len(cell) == 0:
        #             display[i][j] = empty_symbol
        #             continue
        #         if len(cell) == 1:
        #             obj = cell[0]
        #             symbol = find_symbol(obj.definition[0], [obj])
        #             display[i][j] = symbol
        #             continue
        #         if len(cell) >= 2:
        #             objs = cell
        #             symbol = find_symbol('+', objs)
        #             display[i][j] = symbol
        #             continue
        # legend_lines = []
        # max_legend_width = 70
        # for symbol, objs in symbols_used.items():
        #     legend_pair = f'{symbol.strip()} = {" and ".join([f'{obj.definition}{(f" ({', '.join(obj.inventory)})") if obj.inventory else ''}' for obj in objs])}  '
        #     if not legend_lines:
        #         legend_lines.append(legend_pair)
        #         continue
        #     if len(legend_lines[-1] + legend_pair) > max_legend_width:
        #         legend_lines.append(legend_pair)
        #     else:
        #         legend_lines[-1] = legend_lines[-1] + legend_pair
        # legend = '\n'.join(legend_lines)
        # message = f'```\n{'\n'.join([''.join(line) for line in display])}\n\n{legend}```'
        message = WackyCodexDisplayer.draw_ansi(objects_seen, player)
        owner = ctx.focus(str(author.id))
        owner.display_mode = 'a'
        await channel.send(message)

    async def wacky_codex_draw_monochrome(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        try:
            objects_seen = ctx.look_around_as_owned_object(str(author.id))
        except LookupError as err:
            extra_msg = ''
            if 'player-missing' in err.args:
                extra_msg = f'There is no object belonging to you for you to look around as. Maybe try {prefix}wc-start to make one?'
            return await channel.send(f'{err.args[0]}\n{extra_msg}')
        player = ctx.get_object_by_owner(str(author.id))
        ctx.clear_output()
        message = WackyCodexDisplayer.draw(objects_seen, player)
        owner = ctx.focus(str(author.id))
        owner.display_mode = 'd'
        await channel.send(message)

    async def wacky_codex_update(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        owner = ctx.focus(str(author.id))
        output = owner.read_and_clear_output()
        if output:
            await multisend(channel, output)
        else:
            await channel.send('Nothing new has happened.')

    async def wacky_codex_recompile(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if len(args) < 1:
            return await channel.send(f'Correct syntax: {prefix}wc-recompile <word>')
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        word = " ".join(args)
        extra['rawinput'] = ctx.lookup(word, concat=True)
        await self.wacky_codex_define(args, author, channel, monkey, commandlist, extra)

    async def wacky_codex_recompile_all(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if await auth_check_dev_command(channel, author):
            return
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        extra['rawinput'] = f'```{ctx.lookup_all()}```'
        await self.wacky_codex_define(args, author, channel, monkey, commandlist, extra)

    class WackyCodexNewWorld(discord.ui.Modal, title='Create World'):
        world_name = discord.ui.TextInput(label='World Name', placeholder='Type name...', required=True, max_length=30)
        world_type = discord.ui.TextInput(
            label='Generation Type - Type a number',
            min_length=1, max_length=1,
            placeholder='1',
        )

        async def on_submit(self, interaction: Interaction):
            selected_world_type = str(self.world_type)
            selected_world_name = str(self.world_name)
            if selected_world_type not in ['1','2','3']:
                await interaction.response.send_message(f'Invalid world type: {self.world_type}', ephemeral=True)
                await interaction.message.edit(view=None) # type: ignore
                return
            if selected_world_name in all_wacky_contexts:
                await interaction.response.send_message(f'A world with the name {self.world_name} already exists somewhere! You\'ll have to pick a *unique* name for the world.', ephemeral=True)
                await interaction.message.edit(view=None) # type: ignore
                return
            ctx = WackyCodex.Ctx()
            if isinstance(interaction.channel, discord.DMChannel):
                ctx.ctx_created_from = interaction.channel.recipient.global_name # type: ignore
            else:
                ctx.ctx_created_from = interaction.guild.name # type: ignore
            all_wacky_contexts[selected_world_name] = ctx
            data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(interaction.channel), ServerDMData())    # type: ignore
            if selected_world_name not in data.availible_wacky_contexts:
                data.availible_wacky_contexts.append(selected_world_name) # shouldn't happen but it can during development
            data.current_wacky_context_name = selected_world_name
            try:
                if selected_world_type == '1':
                    WackyCodex.compile(WackyCodex.DefaultFile, ctx, add_to_ctx=True, permit_place=True)
                if selected_world_type == '2':
                    pass
                if selected_world_type == '3':
                    WackyCodex.compile(WackyCodex.ExampleFile, ctx, add_to_ctx=True, permit_place=True)
            except WackyCodex.CompilationError as compilation_error:
                await interaction.channel.send(f'Well, crud, a problem happened during the creation of your world (generation type {selected_world_type}) (please contact <@152885068606603265>):\n'+str(compilation_error)) # type: ignore
                await interaction.response.edit_message(view=None)
                data.current_wacky_context_name = None
                all_wacky_contexts.pop(selected_world_name)
                return
            await interaction.response.edit_message(view=None)
            await interaction.channel.send(f'Your world, {selected_world_name}, has been created! Use {prefix}wc-start to create a player in it.') # type: ignore

    async def wacky_codex_new_world(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        the_view = discord.ui.View()
        setup_button = discord.ui.Button(label='Setup')
        the_view.add_item(setup_button)

        the_modal = Commands.WackyCodexNewWorld()

        async def on_click_setup(interaction: discord.Interaction):
            await interaction.response.send_modal(the_modal)
        setup_button.callback = on_click_setup
        
        await channel.send('Create a new world! Select a name for the world, and the generation type.\nFor the generation type, type one of these numbers:\n1. Default (adds some starting objects and definitions)\n2. Zero (start with nothing)\n3. Example World', view=the_view)
    
    async def wacky_codex_current_world(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        if isinstance(channel, discord.DMChannel):
            await channel.send(f'Currently loaded world for this DM channel is {ctx_name}.')
        else:
            await channel.send(f'Currently loaded world for this server is {ctx_name}.')

    async def wacky_codex_scan(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        try: 
            objects_seen = ctx.look_around_as_owned_object(str(author.id))
        except LookupError as err:
            extra_msg = ''
            if 'player-missing' in err.args:
                extra_msg = f'There is no object belonging to you for you to look around as. Maybe try {prefix}wc-start to make one?'
            return await channel.send(f'{err.args[0]}\n{extra_msg}')
        player = ctx.get_object_by_owner(str(author.id))
        ctx.clear_output()
        # description_list = [
        #     f'**{obj.definition}** at {obj.position.str_numbers()} <multiplicity_of_object>{
        #         '\n- '+', '.join(WackyCodex.format_counted(WackyCodex.count_and_deduplicate(obj.inventory))) if obj.inventory else ''
        #     }' for obj in objects_seen
        # ]
        # description_list = WackyCodex.format_counted_special(WackyCodex.count_and_deduplicate(description_list), '<multiplicity_of_object>')
        # message = '\n'.join(description_list)
        message = WackyCodexDisplayer.scan(objects_seen, player)
        owner = ctx.focus(str(author.id))
        owner.display_mode = 's'
        await send_maybe_empty(channel, message)

    async def wacky_codex_omni_scan(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        ctx = all_wacky_contexts[ctx_name]
        objects_seen = ctx.objects
        description_list = [
            f'**{obj.definition}** at {obj.position} <multiplicity_of_object>{
                '\n- '+', '.join(WackyCodex.format_counted(WackyCodex.count_and_deduplicate(obj.inventory))) if obj.inventory else ''
            }' for obj in objects_seen
        ]
        description_list = WackyCodex.format_counted_special(WackyCodex.count_and_deduplicate(description_list), '<multiplicity_of_object>')
        await send_maybe_empty(channel, '\n'.join(description_list))

    async def wacky_codex_dev_list_worlds(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if await auth_check_dev_command(channel, author):
            return
        await send_maybe_empty(channel, '\n'.join(all_wacky_contexts.keys()))

    async def dev_list_server_dm_data(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if await auth_check_dev_command(channel, author):
            return
        await send_maybe_empty(channel, '\n'.join(f'{key}\n{data.__dict__}' for key, data in all_server_dm_data.items()))

    async def wacky_codex_dev_delete_world(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if len(args) < 1:
            return await channel.send(f'Correct syntax: {prefix}wc-dev-delete-world <world name>')
        if await auth_check_dev_command(channel, author):
            return
        name = " ".join(args)
        try:
            all_wacky_contexts.pop(name)
            for data in all_server_dm_data.values():
                if data.current_wacky_context_name == name:
                    data.current_wacky_context_name = None
                try:
                    data.availible_wacky_contexts.remove(name)
                except ValueError:
                    pass
            await channel.send(f'World {name} has been deleted.')
        except KeyError:
            await channel.send(f'There is no world with name {name}.')

    async def wacky_codex_view_worlds(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        load_slot_type = 'DM channel' if isinstance(channel, discord.DMChannel) else 'server'
        availible_worlds = (
            '- ' + '\n- '.join(f'`{world}` from {all_wacky_contexts.get(world, NULL_WACKY_CODEX).ctx_created_from}' for world in server_data.availible_wacky_contexts) 
            if server_data.availible_wacky_contexts 
            else f'No worlds are availible!\nCreate one with `{prefix}wc-new-world` or share one with `{prefix}wc-share-world`.'
        )
        if name := server_data.current_wacky_context_name:
            await channel.send(f'Currently loaded world for this {load_slot_type} is {name}. Availible worlds:\n{availible_worlds}')
        else:
            await channel.send(f'This {load_slot_type} does not currently have a world loaded. Availible worlds:\n{availible_worlds}')

    async def wacky_codex_share_world(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if len(args) < 1:
            return await channel.send(f'Correct syntax: {prefix}wc-share-world <server name OR @mention>')
        message: discord.Message = extra['message']
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        ctx_name = await server_data.get_wacky_context_or_return_message(channel)
        if not ctx_name:
            return
        server_name = ' '.join(args)
        other_name = server_name
        try:
            if message.mentions:
                other_identifier = await ServerDMData.create_identifier_from_user(message.mentions[0])
                other_name = message.mentions[0].global_name
            else:
                other_identifier = ServerDMData.create_identifier_from_server(find_guild(server_name))
            other_data = all_server_dm_data.setdefault(other_identifier, ServerDMData())
            if ctx_name in other_data.availible_wacky_contexts:
                await channel.send(f'**{other_name}** already has access to the world **{ctx_name}**.')
            else:
                other_data.availible_wacky_contexts.append(ctx_name)
                await channel.send(f'Shared the world **{ctx_name}** with **{other_name}**!')
        except ValueError:
            await channel.send(f'I wasn\'t able to find a server with the name **{server_name}**. I might not be in it?')

    async def wacky_codex_dev_clear_worlds(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if await auth_check_dev_command(channel, author):
            return
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        count = len(server_data.availible_wacky_contexts)
        server_data.availible_wacky_contexts.clear()
        await channel.send(f'Removed {count} worlds from availability.')

    async def wacky_codex_switch_world(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if len(args) < 1:
            return await channel.send(f'Correct syntax: {prefix}wc-switch-world <world name>')
        server_data = all_server_dm_data.setdefault(ServerDMData.create_identifier_from_channel(channel), ServerDMData())
        world_name = ' '.join(args)
        if world_name not in server_data.availible_wacky_contexts:
            await channel.send(f'That world is not availible to you. If you expected it to be, make sure it\'s been shared with you: check `{prefix}wc-list-worlds` to see which worlds you can access.')
            return
        server_data.current_wacky_context_name = world_name
        await channel.send(f'Set current world to **{world_name}**!')

    async def dev_cron_now(self, args, author: discord.User, channel: discord.channel.TextChannel, monkey: Monkey, commandlist, extra):
        if await auth_check_dev_command(channel, author):
            return
        slow_loop()
        await channel.send('I did it')

@client.event
async def on_message(message: discord.Message):
    global num_self_responses

    try:
        with open('Data.monkey', 'rb') as thefile:
            monkey = pickle.load(thefile)
    except FileNotFoundError:
        monkey = Monkey()

    rawinput = message.content
    inputchannel = message.channel
    author = message.author

    if author.id == 473588280584306707 : # count self-responses
        num_self_responses += 1
        if num_self_responses == 10:
            await inputchannel.send("LOOP TERMINATED")
        if num_self_responses >= 10:
            return

    if author.id == 292953664492929025 :  # for use with unbelievaboat's $say command
        rawinput = rawinput[1:]

    args = parsecommand(rawinput)

    if (author == bot.user) and not monkey.selfinfluence:
        return


    commands = Commands()
    
    lookupcommand = {
        prefix + "hello": commands.hello,
        prefix + "goodbye": commands.goodbye,
        prefix + "repeatme": commands.repeatme,
        prefix + "clearreactions": commands.clearreactions,
        prefix + "setchannel": commands.setchannel,
        prefix + "telephone": commands.telephone,
        prefix + "debug": commands.debug,
        prefix + "setmystring": commands.setmystring,
        prefix + "mystring": commands.mystring,
        prefix + "honk": commands.null,
        prefix + "scaleofgay": commands.scaleofgay,
        prefix + "randomsong": commands.randomsong,
        prefix + "stop": commands.stop,
        prefix + "randomword": commands.randomword,
        prefix + "playfile": commands.playfile,
        prefix + "help": commands.help,
        prefix + "sendfile": commands.sendfile,
        prefix + "ls": commands.ls,
        prefix + "setkey": commands.setkey,
        prefix + "key": commands.key,
        prefix + "convertkeys": commands.null,
        prefix + "randomkey": commands.randomkey,
        prefix + "doublekey": commands.doublekey,
        prefix + "createdeck": commands.createdeck,
        prefix + "setcard": commands.setcard,
        prefix + "addcard": commands.setcard,
        prefix + "removecard": commands.removecard,
        prefix + "drawdeck": commands.drawdeck,
        prefix + "deck": commands.drawdeck,
        prefix + "draw": commands.drawdeck,
        prefix + "reshuffle": commands.reshuffle,
        prefix + "rolldeck": commands.rolldeck,
        prefix + "roll": commands.rolldeck,
        prefix + "listdecks": commands.listdecks,
        prefix + "spreaddeck": commands.spreaddeck,
        prefix + "spread": commands.spreaddeck,
        prefix + "flipcoin": commands.flipcoin,
        prefix + "embed_test": commands.embed_test,
        prefix + "wc-start": commands.wacky_codex_create_player,
        prefix + "wc-define": commands.wacky_codex_define,
        prefix + "wc-do": commands.wacky_codex_do,
        prefix + "wc": commands.wacky_codex_do,
        prefix + "wc-spawn": commands.wacky_codex_spawn,
        prefix + "wc-lookup": commands.wacky_codex_lookup,
        prefix + "wc-spill": commands.wacky_codex_spill,
        prefix + "wc-look": commands.wacky_codex_look,
        prefix + "wc-draw": commands.wacky_codex_draw,
        prefix + "wc-sketch": commands.wacky_codex_draw_monochrome,
        prefix + "wc-scan": commands.wacky_codex_scan,
        prefix + "wc-update": commands.wacky_codex_update,
        prefix + "wc-recompile": commands.wacky_codex_recompile,
        prefix + "wc-new-world": commands.wacky_codex_new_world,
        prefix + "wc-create-world": commands.wacky_codex_new_world,
        prefix + "wc-omni-scan": commands.wacky_codex_omni_scan,
        prefix + "wc-dev-list-worlds": commands.wacky_codex_dev_list_worlds,
        prefix + "wc-dev-list-all-worlds": commands.wacky_codex_dev_list_worlds,
        prefix + "wc-dev-delete-world": commands.wacky_codex_dev_delete_world,
        prefix + "wc-dev-destroy-world": commands.wacky_codex_dev_delete_world,
        prefix + "wc-current-world": commands.wacky_codex_current_world,
        prefix + "wc-dev-recompile-all": commands.wacky_codex_recompile_all,
        prefix + "wc-view-worlds": commands.wacky_codex_view_worlds,
        prefix + "wc-availible-worlds": commands.wacky_codex_view_worlds,
        prefix + "wc-show-worlds": commands.wacky_codex_view_worlds,
        prefix + "wc-list-worlds": commands.wacky_codex_view_worlds,
        prefix + "wc-share-world": commands.wacky_codex_share_world,
        prefix + "wc-dev-clear-worlds": commands.wacky_codex_dev_clear_worlds,
        prefix + "wc-switch-world": commands.wacky_codex_switch_world,
        prefix + "wc-change-world": commands.wacky_codex_switch_world,
        prefix + "dev-list-server-dm-data": commands.dev_list_server_dm_data,
        prefix + "dev-cron-now": commands.dev_cron_now,
    }

    if args[0] in lookupcommand:
        print(args)
        if author.id != 473588280584306707:
            num_self_responses = 0
        await lookupcommand[args[0]](args[1:], author, inputchannel, monkey, (lookupcommand, commands), extra={'rawinput':rawinput, 'message': message})

    with open("Data.monkey", "wb") as thefile:
        pickle.dump(monkey,thefile)

    if message.type == discord.MessageType.reply and message.reference:
        original_message = None
        if message.reference.cached_message:
            original_message = message.reference.cached_message
        else:
            if isinstance(message.channel, discord.GroupChannel):
                return
            if message.reference is None or message.reference.message_id is None:
                return
            original_message = await message.channel.get_partial_message(message.reference.message_id).fetch()
        if "notifyreply" in original_message.content:
            channel = await original_message.author.create_dm()
            await channel.send(f"Your message was replied to: {original_message.jump_url}")
        for reaction in original_message.reactions:
            emoji_str = str(reaction.emoji)
            print(emoji_str)
            if "notifyreply" in emoji_str:
                async for user in reaction.users():
                    channel = await user.create_dm()
                    await channel.send(f"A message was replied to: {reaction.message.jump_url}") 

@client.event
async def on_reaction_add(reaction: discord.Reaction, user):
    if ("notifyreaction" in reaction.message.content):
        channel = await reaction.message.author.create_dm()
        await channel.send(f"Your message was reacted to: {reaction.message.jump_url}")

def bot_setup():
    global all_wacky_contexts, all_server_dm_data
    try:
        with open('wacky_codices.monkey', 'rb') as thefile:
            all_wacky_contexts = pickle.load(thefile)
            print(f'Loaded {len(all_wacky_contexts)} wacky codices!')
            for ctx_name, ctx in all_wacky_contexts.items():
                upgraded = ctx.set_missing_defaults() # stupid but works
                if upgraded:
                    print(f'Upgraded {ctx_name}: {upgraded}') 
    except FileNotFoundError:
        print('Could not find wacky codices :(')
        all_wacky_contexts = {}
    try:
        with open('server_dm_data.monkey', 'rb') as thefile:
            all_server_dm_data = pickle.load(thefile)
            print(f'Loaded {len(all_server_dm_data)} server/channel data!')
    except FileNotFoundError:
        print('Could not find server/DM data :(')
        all_server_dm_data = {}

def slow_loop():
    global all_wacky_contexts, all_server_dm_data
    with open("wacky_codices.monkey", "wb") as thefile:
        pickle.dump(all_wacky_contexts, thefile)
    with open("server_dm_data.monkey", "wb") as thefile:
        pickle.dump(all_server_dm_data, thefile)
    for ctx in all_wacky_contexts.values():
        if ctx.passive_ticks < config['wacky_codex']["max_passive_ticks"]:
            ctx.tick(passive_tick=True)

@client.event
async def on_ready():
    print("I am ready.")
    print("I am " + client.user.name + ', number ' + str(client.user.id)) # type: ignore
    bot_setup()
    print('Bot Setup Complete')
    while True:
        await asyncio.sleep(config['cron_period_seconds'])
        slow_loop()
    #await client.get_channel(743322729176105060).connect()

printlist(parsecommand("type \"lucky is in the shower\" #general"))
printlist(parsecommand("type \"oh, sure, you're going to the \\\"shower,\\\" yeah of course you are\""))
print("type \"oh, sure, you're going to the \\\"shower,\\\" yeah of course you are\"")

client.run(config['token'])