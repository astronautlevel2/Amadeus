#!/usr/bin/env python3

import os
import sys
import json
from collections import deque

import asyncio
import discord
import youtube_dl

from discord.ext import commands

# Options adapted from audio example in the discord.py repo
ydl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloaded',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ydl = youtube_dl.YoutubeDL(ydl_format_options)
ies = youtube_dl.extractor.gen_extractors()
queue = deque()
skip_votes = set()

try:
    with open("config.json") as c:
        config = json.load(c)
except FileNotFoundError:
    print("Config file not found - please copy config.json.example to config.json")
    sys.exit()

bot = commands.Bot( command_prefix=config['prefix'],
                    description='An open source music bot',
                    max_messages=100)
bot.playing = False

def supported(url):
    for ie in ies:
        if ie.suitable(url) and ie.IE_NAME != 'generic':
            # Site has dedicated extractor
            return True
    return False

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

async def play_internal(ctx, url):
    try:
        os.remove("downloaded")
    except FileNotFoundError:
        pass
    ydl.download([url])
    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("downloaded"))
    await ctx.send(await commands.clean_content().convert(ctx,
                                    "Now playing: {}".format(url)))
    ctx.voice_client.play(source)
    while ctx.voice_client and ctx.voice_client.is_playing():
        await asyncio.sleep(2)

@bot.command()
async def play(ctx, *, url):
    if not ctx.voice_client:
        return await ctx.send("I'm not in a voice channel!")
    if not supported(url):
        return await ctx.send("This is not a valid URL for youtube-dl.")
    queue.appendleft(url)
    await ctx.send(await commands.clean_content().convert(ctx,
                                    "Added {} to the queue!".format(url)))
    if bot.playing: return
    bot.playing = True
    while queue and bot.playing:
        skip_votes.clear()
        url = queue.pop()
        await play_internal(ctx, url)
    await ctx.send("Reached end of queue!")
    bot.playing = False

@bot.command()
async def stop(ctx):
    if bot.playing:
        ctx.voice_client.stop()
        bot.playing = False
        queue.clear()
        await ctx.send("Stopped playing!")
    else:
        await ctx.send("I'm not playing anything!")

@bot.command()
async def skip(ctx):
    if bot.playing:
        if ctx.author == ctx.guild.owner:
            ctx.voice_client.stop()
            await ctx.send("Skipped entry!")
        else:
            skip_votes.add(ctx.author)
            await ctx.send("Added a vote to skip! Current votes: {}. Votes needed: {}".format(len(skip_votes), len(ctx.voice_client.channel.members) // 2))
            if len(skip_votes) >= len(ctx.voice_client.channel.members) // 2:
                ctx.voice_client.stop()
                await ctx.send("Skipped entry!")
    else:
        await ctx.send("I'm not playing anything!")

@bot.command(aliases=['vol'])
async def volume(ctx, *, vol):
    if ctx.voice_client:
        ctx.voice_client.source.volume = int(vol)/100
    else:
        await ctx.send("I'm not in a voice channel!")

@bot.command()
async def queued(ctx):
    msg = "Songs currently in queue: ```"
    for s in queue:
        msg += s + "\n"
    await ctx.send(await commands.clean_content().convert(ctx, msg + "```"))

bot.run(config['token'])
