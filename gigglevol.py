#!/usr/bin/env python
import discord
import re
import asyncio
from settings import bot_token

client = discord.Client()

async def process_vol_message(message):
    category = discord.utils.get(message.guild.channels, name="YOUTUBE")
    content_creators = []
    for channel in category.channels:
        content_creators.append(channel)
    try:
        if len(message.embeds) > 0 and re.search(r'Successfully subscribed to (.*)', message.embeds[0].title):
            channel_name = re.search(r'Successfully subscribed to (.*)', message.embeds[0].title).group(1)
            name = channel_name.replace(' ', '-').lower()
            creator_channel_found = False
            output = ""
            for channel in message.guild.channels:
                if channel.name == channel_name:
                    creator_channel_found = True
            if not creator_channel_found:
                await message.guild.create_text_channel(name=name, category=category)
                output += f"I've created the {name} channel\n"
            output += f"New {channel_name} videos will be posted to the {name} channel\n"
            await message.channel.send(embed=discord.Embed(description=output, color=0x00ff00))
            return
    except:
        await message.channel.send(f"I don't know how to handle {channel_name}'s content.  Please contact my creator to get {channel_name} added to my functionality")
        return

    for channel in message.guild.text_channels:
        if channel.name == 'voice-of-light-posts':
            vol_posts_channel = channel

    try:
        if(message.embeds[0].title == 'Youtube subscriptions'):
            return
    except:
        pass

    if vol_posts_channel == message.channel:
        try:
            creator_name = message.embeds[0].author.name
            channel_name = creator_name.replace(' ', '-').lower()

            creator_channel = discord.utils.get(message.guild.channels, name=channel_name)

            if creator_channel:
                for embed in message.embeds:
                    await creator_channel.send(embed=embed)
            else:
                await vol_posts_channel.send(embed=discord.Embed(description=f"Cannot post to channel {creator_name}", color=0x00ff00))
        except:
            pass

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.author.id == 460410391290314752:
        await process_vol_message(message)

client.run(bot_token)
