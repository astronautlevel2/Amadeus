#!/usr/bin/env python3

import os
import sys
import json

import asyncio
import discord
import youtube_dl

from discord.ext import commands

try:
    with open("config.json") as c:
        config = json.load(c)
except FileNotFoundError:
    print("Config file not found - please copy config.json.example to config.json")
    sys.exit()

bot = commands.Bot( command_prefix=config['prefix'],
                    description='An open source music bot',
                    max_messages=100)

@bot.event
async def on_ready():
    if len(sys.argv) > 1:
        try:
            channel = bot.get_channel(int(sys.argv[1]))
            await channel.send("Bot has restarted")
        except:
            pass

@commands.has_permissions(administrator=True)
@bot.command(hidden=True)
async def restart(ctx):
    await ctx.send("Restarting bot")
    os.execv(__file__, [__file__, str(ctx.channel.id)])

@bot.command()
async def connect(ctx):
    voice = ctx.author.voice
    if not voice:
        await ctx.send("You need to be in a voice channel!")
    elif ctx.voice_client:
        await ctx.voice_client.move_to(voice.channel)
    else:
        await voice.channel.connect()

@bot.command()
async def disconnect(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("I'm not in a voice channel!")

bot.run(config['token'])
