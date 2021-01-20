#!/usr/bin/env python
import settings
import mysql.connector

def db_connect():
    return mysql.connector.connect(
            host="localhost",
            user=settings.db_user,
            password=settings.db_password,
            database=settings.database,
            charset='utf8mb4'
            )

def db_execute_sql(sql, fetch, **kwargs):
    mydb = db_connect()
    mycursor = mydb.cursor(buffered=True)
    mycursor.execute(sql, tuple(kwargs.values()))

    rows = None
    if fetch:
        rows = mycursor.fetchall()

    mydb.commit()
    mycursor.close()
    mydb.disconnect()

    return rows

def get_all(table):
    return db_execute_sql(f"SELECT * FROM {table}", True)

def get_creator_channels():
    return db_execute_sql("SELECT * FROM creator_channels", True)

def save_creator_channel(creator, guild_id, channel_id, role_id):
    db_execute_sql("INSERT INTO creator_channels values ( %s, %s, %s, %s ) ON DUPLICATE KEY UPDATE channel_id = %s, role_id = %s",
            False, creator=creator, guild_id=guild_id, channel_id=channel_id, role_id=role_id, channel_id_2=channel_id, role_id_2=role_id)

def delete_creator_channel(creator, guild_id):
    db_execute_sql("DELETE FROM creator_channels WHERE creator = %s and guild_id = %s", False, creator=creator, guild_id=guild_id)

def add_guild(id, name):
    db_execute_sql("INSERT INTO guilds values ( %s, %s ) ON DUPLICATE KEY UPDATE name = %s", False, id=id, name=name, name_2=name)

def save_user(id, name, last_active, guilds):
    db_execute_sql("INSERT INTO users values ( %s, %s, %s ) ON DUPLICATE KEY UPDATE name = %s, last_active=%s", False, id=id, name=name, last_active=last_active, name_2=name, last_active_2=last_active)
    for guild in guilds:
        db_execute_sql("INSERT INTO user_guilds values ( %s, %s ) ON DUPLICATE KEY UPDATE guild_id = %s", False, user_id=id, guild_id=guild, guild_id_2=guild)

def set_user_last_active(id, last_active):
    db_execute_sql("UPDATE users SET last_active=%s WHERE id = %s", False, last_active=last_active, id=id)
