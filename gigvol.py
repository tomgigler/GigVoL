#!/usr/bin/env python
import discord
import re
import os
import asyncio
from settings import bot_token
import sys
from datetime import datetime
from time import time, ctime
from operator import attrgetter
from hashlib import md5

client = discord.Client()

async def list_user_roles(message):
    youtube_roles = []
    youtube_channels = []
    server_roles = []
    user_roles = []
    youtube_category = discord.utils.get(message.guild.channels, name="YOUTUBE")
    for channel in youtube_category.channels:
        youtube_channels.append(channel.name)
    for role in message.guild.roles:
        server_roles.append(role.name)
    for role in message.author.roles:
        user_roles.append(role.name)
    for name in youtube_channels:
        if name in server_roles and name in user_roles:
            if name not in youtube_roles:
                youtube_roles.append(name)
    if len(youtube_roles) > 0:
        embed = discord.Embed(title=f"{message.author.name}'s roles:", description='\n'.join(youtube_roles), color=0x00ff00)
        await message.channel.send(embed=embed)

async def add_user_role(message):
    add_role = re.search('~gigvol youtube add (.*)', message.content, re.IGNORECASE).group(1)
    youtube_category = discord.utils.get(message.guild.channels, name="YOUTUBE")
    if not discord.utils.get(youtube_category.channels, name=add_role):
        await message.channel.send(embed=discord.Embed(description=f"Cannot add {add_role} role", color=0x00ff00))
        return
    if discord.utils.get(message.author.roles, name=add_role):
        await message.channel.send(embed=discord.Embed(description=f"You already have the {add_role} role", color=0x00ff00))
        return
    else:
        role = discord.utils.get(message.guild.roles, name=add_role)
        await message.author.add_roles(role)
    await asyncio.sleep(1)
    if discord.utils.get(message.author.roles, name=add_role):
        await message.channel.send(embed=discord.Embed(description=f"Added {add_role} role", color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description=f"Failed to add {add_role} role", color=0x00ff00))

async def remove_user_role(message):
    remove_role = re.search('~gigvol youtube remove (.*)', message.content, re.IGNORECASE).group(1)
    youtube_category = discord.utils.get(message.guild.channels, name="YOUTUBE")
    if not discord.utils.get(youtube_category.channels, name=remove_role):
        await message.channel.send(embed=discord.Embed(description=f"Cannot remove {remove_role} role", color=0x00ff00))
        return
    if not discord.utils.get(message.author.roles, name=remove_role):
        await message.channel.send(embed=discord.Embed(description=f"You don't currently have the {remove_role} role", color=0x00ff00))
        return
    else:
        role = discord.utils.get(message.guild.roles, name=remove_role)
        await message.author.remove_roles(role)
    await asyncio.sleep(1)
    if not discord.utils.get(message.author.roles, name=remove_role):
        await message.channel.send(embed=discord.Embed(description=f"Removed {remove_role} role", color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description=f"Failed to remove {remove_role} role", color=0x00ff00))

async def list_roles(message):
    youtube_roles = []
    youtube_channels = []
    server_roles = []
    youtube_category = discord.utils.get(message.guild.channels, name="YOUTUBE")
    for channel in youtube_category.channels:
        youtube_channels.append(channel.name)
    for role in message.guild.roles:
        server_roles.append(role.name)
    for name in youtube_channels:
        if name in server_roles:
            if name not in youtube_roles:
                youtube_roles.append(name)
    if len(youtube_roles) > 0:
        await message.channel.send(embed=discord.Embed(title='Available roles:', description='\n'.join(youtube_roles), color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description='No YouTube roles found', color=0x00ff00))

async def process_vol_message(message):
    server_roles = []
    youtube_category = discord.utils.get(message.guild.channels, name="YOUTUBE")
    content_creators = []
    for channel in youtube_category.channels:
        content_creators.append(channel)
    try:
        if len(message.embeds) > 0 and re.search(r'Successfully subscribed to (.*)', message.embeds[0].title):
            channel_name = re.search(r'Successfully subscribed to (.*)', message.embeds[0].title).group(1)
            name = channel_name.replace(' ', '-').lower()
            creator_role_found = False
            creator_channel_found = False
            output = ""
            for role in message.guild.roles:
                if role.name == channel_name:
                    creator_role_found = True
            for channel in message.guild.channels:
                if channel.name == channel_name:
                    creator_channel_found = True
            if not creator_channel_found:
                await message.guild.create_text_channel(name=name, category=youtube_category)
                output += f"I've created the {name} channel\n"
            if not creator_role_found:
                await message.guild.create_role(name=name)
                output += f"I've created the {name} role\n"
            output += f"New {channel_name} videos will be posted to the {name} channel and ping the {name} role\n"
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
            channel_role_name = creator_name.replace(' ', '-').lower()

            creator_channel = discord.utils.get(message.guild.channels, name=channel_role_name)
            creator_role = discord.utils.get(message.guild.roles, name=channel_role_name)

            if creator_channel:
                if creator_role:
                    await creator_channel.send(creator_role.mention)
                else:
                    await vol_posts_channel.send(embed=discord.Embed(description=f"Cannot ping role {creator_name}", color=0x00ff00))
                for embed in message.embeds:
                    await creator_channel.send(embed=embed)
            else:
                await vol_posts_channel.send(embed=discord.Embed(description=f"Cannot post to channel {creator_name}", color=0x00ff00))
        except:
            pass

async def show_delay_message(message):
    try:
        guild_id = message.guild.id
    except:
        return
    message_found = False
    msg_num = re.search(r'^~gigvol delay show (\S+)', message.content).group(1)
    if guild_id in delayed_messages:
        for msg in delayed_messages[guild_id]:
            if msg.id == msg_num:
                content = f"{msg.message.author.name} scheduled:\n"
                content += re.search(r'^~gigvol delay \d+[^\n]*[\n](.*)', msg.message.content, re.MULTILINE|re.DOTALL).group(1)
                await message.channel.send(content)
                message_found = True
        if not message_found:
            await message.channel.send(embed=discord.Embed(description="Message not found", color=0x00ff00))
    else:
        await message.channel.send(embed=discord.Embed(description="No messages found", color=0x00ff00))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.author.id == 460410391290314752:
        await process_vol_message(message)

    if re.search(r'^~gigvol youtube$', message.content, re.IGNORECASE):
        await message.channel.send("""```Start your message with "~gigvol youtube" followed by one of the commands below:
            roles:
                Show youtube roles currently assigned to you
            add <role>:
                Assign <role> to yourself
            remove <role>:
                Remove <role> from yourself
            list:
                Show available youtube roles on this server```""")

    elif re.search(r'^~gigvol youtube roles$', message.content, re.IGNORECASE):
        await list_user_roles(message)

    elif re.search(r'^~gigvol youtube add \S', message.content, re.IGNORECASE):
        await add_user_role(message)

    elif re.search(r'^~gigvol youtube remove \S', message.content, re.IGNORECASE):
        await remove_user_role(message)

    elif re.search(r'^~gigvol youtube list$', message.content, re.IGNORECASE):
        await list_roles(message)

client.run(bot_token)
