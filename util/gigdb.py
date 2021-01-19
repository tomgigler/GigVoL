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

def get_creator_channels():
    return db_execute_sql("SELECT * FROM creator_channels", True)

def get_users():
    return db_execute_sql("SELECT id, guild_id FROM users, user_guilds WHERE id = user_id", True)

def save_user(user_id, name, guild_id=None, guild_name=None):
    db_execute_sql("INSERT INTO users values ( %s, %s ) ON DUPLICATE KEY UPDATE name = %s", False, user_id=user_id, name=name, name_2=name)
    if guild_id is not None:
        db_execute_sql("INSERT INTO user_guilds values ( %s, %s, %s ) ON DUPLICATE KEY UPDATE guild_name = %s", False, user_id=user_id, guild_id=guild_id, guild_name=guild_name, guild_name_2=guild_name)

def save_creator_channel(creator, guild_id, channel_id, role_id):
    db_execute_sql("INSERT INTO creator_channels values ( %s, %s, %s, %s ) ON DUPLICATE KEY UPDATE channel_id = %s, role_id = %s",
            False, creator=creator, guild_id=guild_id, channel_id=channel_id, role_id=role_id, channel_id_2=channel_id, role_id_2=role_id)

def delete_creator_channel(creator, guild_id):
    db_execute_sql("DELETE FROM creator_channels WHERE creator = %s and guild_id = %s", False, creator=creator, guild_id=guild_id)
