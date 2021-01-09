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

def get_creator_channels():
    mydb = db_connect()
    mycursor = mydb.cursor()

    mycursor.execute("SELECT * FROM creator_channels")

    rows =  mycursor.fetchall()

    mycursor.close()
    mydb.disconnect()

    return rows

def get_users():
    mydb = db_connect()
    mycursor = mydb.cursor()

    mycursor.execute("SELECT id, guild_id FROM users, user_guilds WHERE id = user_id")

    rows = mycursor.fetchall()

    mycursor.close()
    mydb.disconnect()

    return rows

def save_user(user_id, name, guild_id, guild_name):

    mydb = db_connect()
    mycursor = mydb.cursor(buffered=True)

    sql = "SELECT * FROM users WHERE id = %s"

    mycursor.execute(sql, ( user_id, ))

    if mycursor.rowcount > 0:
        update = True
    else:
        update = False

    if update:
        sql = "UPDATE users SET name = %s WHERE id = %s"
    else:
        sql = "INSERT INTO users ( name, id ) values ( %s, %s )"

    mycursor.execute(sql, ( name, user_id ) )

    sql = "SELECT * FROM user_guilds WHERE user_id = %s and guild_id = %s"

    mycursor.execute(sql, ( user_id, guild_id ) )

    if mycursor.rowcount > 0:
        update = True
    else:
        update = False

    if update:
        sql = "UPDATE user_guilds SET guild_name = %s WHERE user_id = %s and guild_id = %s"
    else:
        sql = "INSERT INTO user_guilds ( guild_name, user_id, guild_id ) values ( %s, %s, %s )"

    mycursor.execute(sql, ( guild_name, user_id, guild_id ) )

    mydb.commit()

    mycursor.close()
    mydb.disconnect()

def save_creator_channel(creator, guild_id, channel_id, role_id):

    mydb = db_connect()
    mycursor = mydb.cursor(buffered=True)

    sql = "SELECT * from creator_channels WHERE creator = %s and guild_id = %s"

    mycursor.execute(sql, ( creator, guild_id ) )

    if mycursor.rowcount > 0:
        update = True
    else:
        update = False

    if update:
        sql = "UPDATE creator_channels SET channel_id = %s, role_id = %s WHERE creator = %s and guild_id = %s"
    else:
        sql = "INSERT INTO creator_channels ( channel_id, role_id, creator, guild_id ) values ( %s, %s, %s, %s )"

    mycursor.execute(sql, ( channel_id, role_id, creator, guild_id ) )

    mydb.commit()
    mycursor.close()
    mydb.disconnect()

def delete_creator_channel(creator, guild_id):

    sql = "DELETE FROM creator_channels WHERE creator = %s and guild_id = %s"

    mydb = db_connect()
    mycursor = mydb.cursor()

    mycursor.execute(sql, ( creator, guild_id ) )

    mydb.commit()

    mycursor.close()
    mydb.disconnect()

