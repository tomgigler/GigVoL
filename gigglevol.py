#!/usr/bin/env python
import discord
import re
import asyncio
from traceback import format_exc
from settings import bot_token
from gigdb import db_connect

creator_channels = {}
users = {}

client = discord.Client()

def load_from_db():
    mydb = db_connect()

    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM creator_channels")

    # Store channel_id and role_id as a tuple in creator_channels dictionary with tuple key (creator, guild_id)
    for row in mycursor.fetchall():
        creator_channels[(row[0], row[1])] = ( row[2], row[3] )

    mycursor.execute("SELECT id, guild_id FROM users, user_guilds WHERE id = user_id")

    for row in mycursor.fetchall():
        if row[0] in users.keys():
            users[row[0]].append(row[1])
        else:
            users[row[0]] = [ row[1] ]

    mycursor.close()
    mydb.disconnect()

async def set_creator_channel(msg, creator, channel_name, role_name=None):
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

    mydb = db_connect()

    mycursor = mydb.cursor()

    if ( creator, msg.guild.id ) in creator_channels.keys():
        sql = "UPDATE creator_channels SET channel_id = %s, role_id = %s WHERE creator = %s and guild_id = %s"
    else:
        sql = "INSERT INTO creator_channels ( channel_id, role_id, creator, guild_id ) values ( %s, %s, %s, %s )"

    mycursor.execute(sql, ( channel.id, role_id, creator, msg.guild.id ) )

    mydb.commit()
    mycursor.close()
    mydb.disconnect()

    creator_channels[(creator, msg.guild.id)] = ( channel.id, role_id )

    if role_name:
        await msg.channel.send(embed=discord.Embed(description=f"**{creator}** videos will be posted to the **{channel_name}** channel and mention the {role_name} role", color=0x00ff00))
    else:
        await msg.channel.send(embed=discord.Embed(description=f"**{creator}** videos will be posted to the **{channel_name}** channel", color=0x00ff00))

async def process_vol_message(msg):
    creator = None
    if msg.embeds[0].footer.text == "Youtube":
        creator = msg.embeds[0].author.name
    if msg.embeds[0].footer.text == "Twitch":
        creator = msg.embeds[0].description

    if (creator, msg.guild.id) in creator_channels.keys():
        creator_channel_id, role_id = creator_channels[(creator, msg.guild.id)]
        creator_channel = msg.guild.get_channel(creator_channel_id)

        for embed in msg.embeds:
            # This is where we will (eventually) mention a role
            await creator_channel.send(embed=embed)

    # deal with sub

    # deal with unsub


    #deal with list (maybe match to channel

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
                output += f"**{creator}:**  {channel.name}  {role_name}\n"
    if output != "":
        output = "**Creator channels**\n=======================\n" + output
        await msg.channel.send(embed=discord.Embed(description=output, color=0x00ff00))

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('with thegigler'))

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if msg.author.id == 460410391290314752:
        await process_vol_message(msg)
        return

    if msg.author.id in users.keys() and msg.guild.id in users[msg.author.id]:
        try:
            match = re.match(r'test +(\d+)', msg.content)
            if match:
                vol_msg = await msg.channel.fetch_message(int(match.group(1)))
                await process_vol_message(vol_msg)
                return

            if re.match(r'^~gigvol +list *$', msg.content):
                await list_creator_channels(msg)

            match = re.match(r'^~gigvol +setchannel +"([^"]+)" +(\S+) *$', msg.content)
            if match:
                if match.group(1) and match.group(2):
                    await set_creator_channel(match.group(1), match.group(2), msg)
                return

        except:
            await msg.channel.send(f"`{format_exc()}`")
            # await msg.channel.send(embed=discord.Embed(description=f"Whoops!  Something went wrong.  Please contact {client.user.mention} for help", color=0xff0000))
            # await client.get_user(669370838478225448).send(f"{msg.author.mention} hit an unhandled exception in the {msg.guild.name} server\n\n`{format_exc()}`")


load_from_db()

client.run(bot_token)
