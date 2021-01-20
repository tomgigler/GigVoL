#!/usr/bin/env python
import discord
import re
import asyncio
from time import time
from traceback import format_exc
from settings import bot_token
from confirm import confirm_request, process_reaction
import gigdb
import giguser
import settings
import help

class GigException(Exception):
    pass

creator_channels = {}

client = discord.Client()

def get_role_id_by_name_or_id(guild, role_param):
    role = discord.utils.get(guild.roles, name=role_param)
    if not role:
        try:
            role = discord.utils.get(guild.roles, id=int(re.search(r'(\d+)', role_param).group(1)))
        except:
            pass
    if not role:
        raise GigException(f"Cannot find {role_param} role")
    return role.id

def get_channel_by_name_or_id(guild, channel_param):
    channel = discord.utils.get(guild.channels, name=channel_param)
    if not channel:
        try:
            channel = discord.utils.get(guild.channels, id=int(re.search(r'(\d+)', channel_param).group(1)))
        except:
            pass
    if not channel:
        raise GigException(f"Cannot find {channel_param} channel")
    #check channel permissions
    if not channel.permissions_for(channel.guild.get_member(client.user.id)).send_messages:
        raise GigException(f"**{client.user.name}** does not have permission to send messages in {channel.mention}")

    return channel

def load_from_db():
    for row in gigdb.get_creator_channels():
        creator_channels[(row[0], row[1])] = ( row[2], row[3] )

    giguser.load_users()

async def set_creator_channel(msg, creator, channel_name, role_name=None):
    creator = creator.lower()
    channel = get_channel_by_name_or_id(msg.guild, channel_name)

    # pinging a role is optional
    if role_name is None:
        role_id = None
    else:
        role_id = get_role_id_by_name_or_id(msg.guild, role_name)

    gigdb.save_creator_channel(creator, msg.guild.id, channel.id, role_id)

    creator_channels[(creator, msg.guild.id)] = ( channel.id, role_id )

    if role_name:
        await msg.channel.send(embed=discord.Embed(description=f"**{creator}** videos will be posted to the **{channel.name}** channel and mention the **{role_name}** role", color=0x00ff00))
    else:
        await msg.channel.send(embed=discord.Embed(description=f"**{creator}** videos will be posted to the **{channel.name}** channel", color=0x00ff00))

async def unset_creator_channel(msg, creator):

    creator = creator.lower()
    if ( creator, msg.guild.id ) in creator_channels.keys():
        if not await confirm_request(msg.channel, msg.author.id, f"Remove {client.user.name} settings for channel {creator}?", 20, client):
            return

        gigdb.delete_creator_channel(creator, msg.guild.id)

        creator_channels.pop((creator, msg.guild.id))

        await msg.channel.send(embed=discord.Embed(description=f"Deleted {creator}", color=0x00ff00))

    else:
        await msg.channel.send(embed=discord.Embed(description=f"Cannot find {creator}", color=0x00ff00))

async def process_vol_message(msg):
    if len(msg.embeds) == 0:
        return
    creator = None
    if msg.embeds[0].footer.text == "Youtube":
        creator = msg.embeds[0].author.name.lower()
    if msg.embeds[0].footer.text == "Twitch":
        creator = msg.embeds[0].description.lower()

    if (creator, msg.guild.id) in creator_channels.keys():
        creator_channel_id, role_id = creator_channels[(creator, msg.guild.id)]
        creator_channel = msg.guild.get_channel(creator_channel_id)
        if role_id:
            creator_role = msg.guild.get_role(role_id)
            await creator_channel.send(creator_role.mention)

        for embed in msg.embeds:
            await creator_channel.send(embed=embed)

        return

    match = re.match(r'^Successfully (un)?subscribed (to|from) (.+)', msg.embeds[0].title)
    if match:
        creator = match.group(3)
        if not match.group(1):
            if (creator.lower(), msg.guild.id) in creator_channels.keys():
                creator_channel_id, role_id = creator_channels[(creator, msg.guild.id)]
                channel_name = msg.guild.get_channel(creator_channel_id)
                if role_id:
                    await msg.channel.send(embed=discord.Embed(description=f"**{creator}** videos will be posted to the **{channel_name}** channel and mention the **{msg.guild.get_role(role_id)}** role", color=0x00ff00))
                else:
                    await msg.channel.send(embed=discord.Embed(description=f"**{creator}** videos will be posted to the **{channel_name}** channel", color=0x00ff00))
            else:
                await msg.channel.send(embed=discord.Embed(description=f"You do not currently have a **{client.user.name}** channel set up for **{creator}** posts\n\nTo set up a channel:\n\n`;giggle set {creator} <channel name or id>`\n\nYou may also set a role to be mentioned for **{creator}** posts.  For more information type `;giggle help`", color=0x00ff00))
        else:
            if (creator.lower(), msg.guild.id) in creator_channels.keys():
                unset_creator_channel(msg, creator)
        return

    #deal with list (maybe match to channel)

async def list_creator_channels(msg):
    output = ""
    for creator, guild_id in creator_channels.keys():
        if guild_id == msg.guild.id:
            channel_id, role_id = creator_channels[(creator, guild_id)]
            channel = msg.guild.get_channel(channel_id)

            role_name = None
            if role_id:
                role = msg.guild.get_role(role_id)
                role_name = role.name
            if channel:
                output += f"> **{creator} - {channel.name} - {role_name}**\n"
    if output != "":
        output = "> **Creator - Channel - Role**\n> =======================\n" + output
        await msg.channel.send(output)
    else:
        output = "No creator channels set"
        await msg.channel.send(embed=discord.Embed(description=output, color=0x00ff00))

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('with thegigler'))

@client.event
async def on_reaction_add(reaction, user):
    if user.id in giguser.users.keys() and reaction.message.guild.id in giguser.users[user.id].guilds:
        process_reaction(reaction.message.id, user.id, reaction.emoji)

@client.event
async def on_guild_join(guild):
    user = client.get_user(settings.bot_owner_id)
    await user.send(f"{client.user.name} bot joined {guild.name}/{guild.id}")

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if isinstance(msg.channel, discord.channel.DMChannel):
        user = client.get_user(settings.bot_owner_id)
        await user.send(f"{msg.author.mention} said {msg.content}")
        return

    if msg.author.id == 460410391290314752:
        await process_vol_message(msg)
        return

    if re.match(r';(giggle|g |g$)', msg.content):
        if msg.author.id not in giguser.users.keys():
            giguser.create_user(msg.author.id, msg.author.name, 0)
        if time() - giguser.users[msg.author.id].last_active > 600 and msg.author.id != settings.bot_owner_id:
            await client.get_user(settings.bot_owner_id).send(f"{msg.author.mention} is interacting with {client.user.mention} in the {msg.guild.name} server")
            giguser.users[msg.author.id].set_last_active(time())

        if giguser.users[msg.author.id] and msg.guild.id in giguser.users[msg.author.id].guilds:
            try:
                # TODO: Return error if number of " is odd
                match = re.match(r';g(iggle)? +test +(\d+)', msg.content)
                if match:
                    vol_msg = await msg.channel.fetch_message(int(match.group(2)))
                    await process_vol_message(vol_msg)
                    return

                match = re.match(r'^;g(iggle)? +adduser +(\S+)( +(\S+))? *$', msg.content)
                if match and msg.author.id == settings.bot_owner_id:
                    if match.group(3):
                        guild_id = int(match.group(3))
                    else:
                        guild_id = msg.guild.id
                    if int(match.group(2)) not in giguser.users.keys():
                        giguser.create_user(int(match.group(2)), client.get_user(int(match.group(2))).name, time())
                    giguser.users[int(match.group(2))].add_guild(guild_id, client.get_guild(guild_id).name)
                    await msg.channel.send(f"Permissions granted for {client.get_user(int(match.group(2))).name} in {client.get_guild(guild_id).name}")
                    return

                if re.match(r'^;g(iggle)? +invite *$', msg.content):
                    await msg.channel.send(discord.utils.oauth_url(client.user.id, permissions=discord.Permissions(permissions=18496)))
                    return

                if re.match(r'^;g(iggle)? +list *$', msg.content):
                    await list_creator_channels(msg)
                    return

                match = re.match(r'^;g(iggle)? +set', msg.content)
                if match:
                    message_content = msg.content
                    role_name = None
                    role_group = None
                    # capture role, if supplied
                    role_provided = re.match(r'.*role\s*=', message_content)
                    if role_provided:
                        # first look for role surrounded by quotes
                        role_match = re.match(r'.*(role\s*=\s*"([^"]+)")', message_content)
                        if role_match:
                            role_group = role_match.group(1)
                            role_name = role_match.group(2)
                        else:
                            # else look for role without quotes
                            role_match = re.match(r'.*(role\s*=\s*([^\s"]+))', message_content)
                            if role_match:
                                role_group = role_match.group(1)
                                role_name = role_match.group(2)
                                # TODO: Deal with the case when 'role\s*=' was provided, but a role could not be parsed
                        if role_group:
                            # strip role group from message_content
                            message_content = message_content.replace(role_group, '')

                    match = re.match(r';g(iggle)? +set? +(.*\S) +(\S+) *$', message_content)
                    if match.group(2) and match.group(3):
                        await set_creator_channel(msg, match.group(2), match.group(3), role_name)
                    return

                match = re.match(r'^;g(iggle)? +unset +(.+)$', msg.content)
                if match:
                    await unset_creator_channel(msg, match.group(2))
                    return

                match = re.match(r';g(iggle)? +(help|\?) *$', msg.content)
                if match:
                    await msg.channel.send(embed=discord.Embed(description=f"{help.show_help()}", color=0x00ff00))
                    return

            except GigException as e:
                await msg.channel.send(embed=discord.Embed(description=str(e), color=0xff0000))
                return

            except:
                await msg.channel.send(embed=discord.Embed(description=f"Whoops!  Something went wrong.  Please contact {client.user.mention} for help", color=0xff0000))
                await client.get_user(settings.bot_owner_id).send(f"{msg.author.mention} hit an unhandled exception in the {msg.guild.name} server\n\n`{format_exc()}`")
                return

            await msg.channel.send(embed=discord.Embed(description="Invalid command.  To see help type:\n\n`;giggle help`", color=0xff0000))

        else:
            await msg.channel.send(embed=discord.Embed(description=f"You do not have premission to interact with me on this server\n\nDM {client.user.mention} to request permission\n\nPlease include the server id ({msg.guild.id}) in your message", color=0xff0000))

load_from_db()

client.run(bot_token)
