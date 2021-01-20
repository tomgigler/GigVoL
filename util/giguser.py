#!/usr/bin/env python
import gigdb

users = {}

class User:
    def __init__(self, id, name=None, last_active=None, guilds=[]):
        self.id = id
        self.name = name
        self.last_active = last_active
        self.guilds = guilds

    def set_last_active(self, last_active):
        gigdb.set_user_last_active(self.id, last_active)
        self.last_active = last_active

    def add_guild(self, guild_id, guild_name):
        gigdb.add_guild(guild_id, guild_name)
        self.guilds.append(guild_id)
        self.save()

    def save(self):
        gigdb.save_user(self.id, self.name, self.last_active, self.guilds)

def load_users():
    for user in gigdb.get_all("users"):
        users[user[0]] = User(user[0], user[1], user[2])

    for row in gigdb.get_all("user_guilds"):
        users[row[0]].guilds.append(row[1])

def create_user(id, name=None, last_active=None, guilds=[]):
    users[id] = User(id, name, last_active, guilds)
    users[id].save()
