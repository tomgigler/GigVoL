#!/usr/bin/env python
import discord
import re
import asyncio
from traceback import format_exc
from settings import bot_token
from confirm import confirm_request, process_reaction
import gigdb

creator_channels = {}
users = {}

client = discord.Client()

def load_from_db():
    for row in gigdb.get_creator_channels():
        creator_channels[(row[0], row[1])] = ( row[2], row[3] )

    for row in gigdb.get_users():
        if row[0] in users.keys():
            users[row[0]].append(row[1])
        else:
            users[row[0]] = [ row[1] ]

async def set_creator_channel(msg, creator, channel_name, role_name=None):
    creator = creator.lower()
    channel = discord.utils.get(msg.guild.channels, name=channel_name)
    if not channel:
        await msg.channel.send(embed=discord.Embed(description=f"Cannot find {channel_name} channel", color=0xff0000))
        return

    # pinging a role is optional
    role_id = None
    if role_name:
        role = discord.utils.get(msg.guild.roles, name=role_name)
        if not role:
            await msg.channel.send(embed=discord.Embed(description=f"Cannot find {role_name} role", color=0xff0000))
            return
        role_id = role.id

    gigdb.save_creator_channel(creator, msg.guild.id, channel.id, role_id)

    creator_channels[(creator, msg.guild.id)] = ( channel.id, role_id )

    if role_name:
        await msg.channel.send(embed=discord.Embed(description=f"**{creator}** videos will be posted to the **{channel_name}** channel and mention the **{role_name}** role", color=0x00ff00))
    else:
        await msg.channel.send(embed=discord.Embed(description=f"**{creator}** videos will be posted to the **{channel_name}** channel", color=0x00ff00))

async def unset_creator_channel(params):
    msg = params['msg']
    creator = params['creator']
    confirmed = params['confirmed']

    creator = creator.lower()
    if ( creator, msg.guild.id ) in creator_channels.keys():
        if not confirmed:
            await confirm_request(msg.channel, msg.author, f"Remove {client.user.name} settings for channel {creator}?", 20, unset_creator_channel, { 'msg': msg, 'creator': creator, 'confirmed': True}, client)
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
        if not match.group(1):
            await msg.channel.send(embed=discord.Embed(description=f"You should consider setting up a {client.user.name} channel for {match.group(3)}", color=0x00ff00))
        else:
            if (match.group(3).lower(), msg.guild.id) in creator_channels.keys():
                await confirm_request(msg.channel, None, f"Remove {client.user.name} settings for channel {match.group(3)}?", 20, unset_creator_channel, { 'msg': msg, 'creator': match.group(3), 'confirmed': True}, client)
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
        await process_reaction(reaction, user, client)

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if msg.author.id == 460410391290314752:
        await process_vol_message(msg)
        return

    if msg.author.id in users.keys() and msg.guild.id in users[msg.author.id] and re.match(r'^;g(iggle)?[ $]', msg.content):
        try:
            match = re.match(r';g(iggle)? +test +(\d+)', msg.content)
            if match:
                vol_msg = await msg.channel.fetch_message(int(match.group(2)))
                await process_vol_message(vol_msg)
                return

            if re.match(r'^;g(iggle)? +list *$', msg.content):
                await list_creator_channels(msg)
                return

            match = re.match(r'^;g(igle)? +set(channel)?', msg.content)
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

                match = re.match(r';g(igle)? +set(channel)? +(.+) +(\S+) *$', message_content)
                if match.group(3) and match.group(4):
                    await set_creator_channel(msg, match.group(3), match.group(4), role_name)
                return

            match = re.match(r'^;g(iggle)? +unset(channel)? +(.+)$', msg.content)
            if match:
                await unset_creator_channel({ 'msg': msg, 'creator': match.group(3), 'confirmed': False})
                return

        except:
            await msg.channel.send(f"`{format_exc()}`")
            # await msg.channel.send(embed=discord.Embed(description=f"Whoops!  Something went wrong.  Please contact {client.user.mention} for help", color=0xff0000))
            # await client.get_user(669370838478225448).send(f"{msg.author.mention} hit an unhandled exception in the {msg.guild.name} server\n\n`{format_exc()}`")


load_from_db()

client.run(bot_token)
